# notifications/services.py

import logging
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import SMSNotification, NotificationTemplate

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@medcare.com')

    def send_email_notification(self, to_email, subject, message, notification_type='general', recipient=None):
        """Send email notification and log it to the DB."""
        # Create the notification record
        notification = SMSNotification.objects.create(
            recipient=recipient,
            phone_number=to_email,  # Using phone_number field for email temporarily
            message=message,
            notification_type=notification_type,
            scheduled_at=timezone.now()
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at'])
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Email send failed to {to_email}: {e}")
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save(update_fields=['status', 'error_message'])
            return False

    def send_medication_reminder(self, prescription, scheduled_datetime):
        """Send a medication reminder email."""
        tpl = NotificationTemplate.objects.filter(
            notification_type='medication_reminder', is_active=True
        ).first()

        if tpl:
            body = tpl.template.format(
                patient_name=prescription.patient.get_full_name(),
                medication_name=prescription.medication.name,
                dosage=prescription.dosage,
                time=scheduled_datetime.strftime('%I:%M %p')
            )
        else:
            body = (
                f"Reminder: time to take your {prescription.medication.name} "
                f"({prescription.dosage}) at {scheduled_datetime.strftime('%I:%M %p')}."
            )

        subject = f"Medication Reminder - {prescription.medication.name}"
        
        return self.send_email_notification(
            to_email=prescription.patient.email,
            subject=subject,
            message=body,
            notification_type='medication_reminder',
            recipient=prescription.patient
        )

    def send_missed_medication_alert(self, prescription, scheduled_datetime):
        """Send a missed medication alert email."""
        tpl = NotificationTemplate.objects.filter(
            notification_type='missed_medication', is_active=True
        ).first()

        if tpl:
            body = tpl.template.format(
                patient_name=prescription.patient.get_full_name(),
                medication_name=prescription.medication.name,
                time=scheduled_datetime.strftime('%I:%M %p')
            )
        else:
            body = (
                f"Alert: you missed your {prescription.medication.name} scheduled for "
                f"{scheduled_datetime.strftime('%I:%M %p')}. Please take it ASAP."
            )

        subject = f"Missed Medication Alert - {prescription.medication.name}"
        
        return self.send_email_notification(
            to_email=prescription.patient.email,
            subject=subject,
            message=body,
            notification_type='missed_medication',
            recipient=prescription.patient
        )
