from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from .models import ProgressReport
from .services import report_generator

User = get_user_model()

class ReportListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProgressReport
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_patients or self.request.user.is_patient
    
    def get_queryset(self):
        if self.request.user.can_manage_patients:
            return ProgressReport.objects.all().order_by('-created_at')
        else:
            return ProgressReport.objects.filter(
                patient=self.request.user
            ).order_by('-created_at')

@login_required
def generate_patient_report(request, patient_id):
    if not request.user.can_manage_patients:
        messages.error(request, "Access denied.")
        return redirect('medications:dashboard')
    
    patient = get_object_or_404(User, id=patient_id, user_type='patient')
    
    # Generate weekly report by default
    report = report_generator.generate_patient_progress_report(
        patient=patient,
        report_type='weekly_summary',
        days=7
    )
    
    messages.success(request, f"Progress report generated for {patient.get_full_name()}")
    return redirect('reports:report_list')

@login_required
def download_report_pdf(request, report_id):
    report = get_object_or_404(ProgressReport, id=report_id)
    
    # Check permissions
    if not (request.user.can_manage_patients or request.user == report.patient):
        raise Http404("Report not found")
    
    if not report.pdf_file:
        messages.error(request, "PDF file not available for this report")
        return redirect('reports:report_list')
    
    try:
        with open(report.pdf_file.path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
            return response
    except FileNotFoundError:
        messages.error(request, "PDF file not found")
        return redirect('reports:report_list')