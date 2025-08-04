# notifications/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth import get_user_model

from .models import SMSNotification
from .services import SMSService  # ← changed

User = get_user_model()

class NotificationHistoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SMSNotification
    template_name = 'notifications/history.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def test_func(self):
        return self.request.user.can_manage_patients

    def get_queryset(self):
        return SMSNotification.objects.all().order_by('-created_at')


@login_required
def send_manual_notification(request):
    if not request.user.can_manage_patients:
        messages.error(request, "Access denied.")
        return redirect('medications:dashboard')

    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        message = request.POST.get('message')

        try:
            patient = User.objects.get(id=patient_id, user_type='patient')
            if not patient.phone_number:
                messages.error(request, "Patient doesn't have a phone number")
            else:
                sms = SMSService()  # ← instantiate here
                success = sms.send_sms(
                    to_number=patient.phone_number,
                    message=message,
                    notification_type='general',
                    recipient=patient
                )

                if success:
                    messages.success(request, f"Notification sent to {patient.get_full_name()}")
                else:
                    messages.error(request, "Failed to send notification")

        except User.DoesNotExist:
            messages.error(request, "Patient not found")

        return redirect('medications:admin_dashboard')

    patients = User.objects.filter(user_type='patient', is_active=True)
    return render(request, 'notifications/send_manual.html', {'patients': patients})
