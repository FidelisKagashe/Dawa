from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count
from datetime import datetime, timedelta
import logging

from .models import Prescription, MedicationIntake, Medication, MedicationSchedule
from .forms import PrescriptionForm, MedicationIntakeForm
from accounts.models import User, PatientProfile

logger = logging.getLogger(__name__)

class PatientDashboardView(LoginRequiredMixin, ListView):
    template_name = 'medications/patient_dashboard.html'
    context_object_name = 'upcoming_medications'
    
    def get_queryset(self):
        if not self.request.user.is_patient:
            return MedicationIntake.objects.none()
        
        today = timezone.now().date()
        return MedicationIntake.objects.filter(
            prescription__patient=self.request.user,
            prescription__is_active=True,
            scheduled_datetime__date=today,
            status='pending'
        ).order_by('scheduled_datetime')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_patient:
            # Get today's medications
            today = timezone.now().date()
            context['todays_medications'] = MedicationIntake.objects.filter(
                prescription__patient=user,
                prescription__is_active=True,
                scheduled_datetime__date=today
            ).order_by('scheduled_datetime')
            
            # Get recent history
            context['recent_history'] = MedicationIntake.objects.filter(
                prescription__patient=user,
                status__in=['taken', 'missed', 'skipped']
            ).order_by('-scheduled_datetime')[:10]
            
            # Get active prescriptions
            context['active_prescriptions'] = Prescription.objects.filter(
                patient=user,
                is_active=True
            ).order_by('-created_at')
            
            # Compliance stats
            week_ago = timezone.now() - timedelta(days=7)
            total_medications = MedicationIntake.objects.filter(
                prescription__patient=user,
                scheduled_datetime__gte=week_ago,
                status__in=['taken', 'missed', 'skipped']
            ).count()
            
            taken_medications = MedicationIntake.objects.filter(
                prescription__patient=user,
                scheduled_datetime__gte=week_ago,
                status='taken'
            ).count()
            
            context['compliance_rate'] = round((taken_medications / total_medications * 100) if total_medications > 0 else 0, 1)
        
        return context

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'medications/admin_dashboard.html'
    context_object_name = 'patients'
    
    def test_func(self):
        return self.request.user.can_manage_patients
    
    def get_queryset(self):
        return User.objects.filter(user_type='patient', is_active=True).order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dashboard statistics
        context['total_patients'] = User.objects.filter(user_type='patient', is_active=True).count()
        context['active_prescriptions'] = Prescription.objects.filter(is_active=True).count()
        context['pending_intakes'] = MedicationIntake.objects.filter(
            status='pending',
            scheduled_datetime__lt=timezone.now()
        ).count()
        
        # Recent activities
        context['recent_prescriptions'] = Prescription.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]
        
        # Staff management for Hospital IT
        if self.request.user.can_manage_staff:
            context['total_staff'] = User.objects.filter(user_type='admin', is_active=True).count()
            context['recent_staff'] = User.objects.filter(user_type='admin', is_active=True).order_by('-date_joined')[:5]
        
        return context

class PrescriptionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = 'medications/prescription_form.html'
    
    def test_func(self):
        return self.request.user.can_manage_patients
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create medication schedules based on frequency
        self.create_medication_schedules(form.instance)
        
        messages.success(self.request, "Prescription created successfully!")
        logger.info(f"Prescription created for {form.instance.patient} by {self.request.user}")
        
        return response
    
    def create_medication_schedules(self, prescription):
        """Create medication schedules based on frequency"""
        frequency_times = {
            'once_daily': ['09:00'],
            'twice_daily': ['09:00', '21:00'],
            'three_times_daily': ['08:00', '14:00', '20:00'],
            'four_times_daily': ['08:00', '12:00', '16:00', '20:00'],
            'every_6_hours': ['06:00', '12:00', '18:00', '00:00'],
            'every_8_hours': ['08:00', '16:00', '00:00'],
            'every_12_hours': ['08:00', '20:00'],
        }
        
        times = frequency_times.get(prescription.frequency, ['09:00'])
        
        for time_str in times:
            hour, minute = map(int, time_str.split(':'))
            scheduled_time = timezone.datetime.strptime(time_str, '%H:%M').time()
            
            MedicationSchedule.objects.create(
                prescription=prescription,
                scheduled_time=scheduled_time
            )
    
    def get_success_url(self):
        return f"/medications/admin/patient/{self.object.patient.id}/"

@login_required
def confirm_medication_intake(request, intake_id):
    intake = get_object_or_404(MedicationIntake, id=intake_id)
    
    if request.user != intake.prescription.patient:
        messages.error(request, "You can only confirm your own medications.")
        return redirect('medications:dashboard')
    
    if request.method == 'POST':
        intake.status = 'taken'
        intake.actual_datetime = timezone.now()
        intake.notes = request.POST.get('notes', '')
        intake.save()
        
        messages.success(request, f"Medication intake confirmed for {intake.prescription.medication.name}")
        logger.info(f"Medication intake confirmed: {intake}")
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'})

class PatientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'medications/patient_detail.html'
    context_object_name = 'patient'
    
    def test_func(self):
        return self.request.user.can_manage_patients
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.get_object()
        
        context['active_prescriptions'] = Prescription.objects.filter(
            patient=patient,
            is_active=True
        ).order_by('-created_at')
        
        context['recent_intakes'] = MedicationIntake.objects.filter(
            prescription__patient=patient
        ).order_by('-scheduled_datetime')[:20]
        
        # Compliance calculation
        week_ago = timezone.now() - timedelta(days=7)
        total_medications = MedicationIntake.objects.filter(
            prescription__patient=patient,
            scheduled_datetime__gte=week_ago,
            status__in=['taken', 'missed', 'skipped']
        ).count()
        
        taken_medications = MedicationIntake.objects.filter(
            prescription__patient=patient,
            scheduled_datetime__gte=week_ago,
            status='taken'
        ).count()
        
        context['compliance_rate'] = round((taken_medications / total_medications * 100) if total_medications > 0 else 0, 1)
        
        return context

class MedicationHistoryView(LoginRequiredMixin, ListView):
    template_name = 'medications/medication_history.html'
    context_object_name = 'medication_history'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.is_patient:
            return MedicationIntake.objects.filter(
                prescription__patient=self.request.user
            ).order_by('-scheduled_datetime')
        return MedicationIntake.objects.none()