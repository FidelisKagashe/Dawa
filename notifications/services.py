import logging
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from .models import SMSNotification, NotificationTemplate

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")

    def send_sms_notification(self, phone_number, message, notification_type='general', recipient=None):
        """Send SMS notification and log it to the DB."""
        # Create the notification record
        notification = SMSNotification.objects.create(
            recipient=recipient,
            phone_number=phone_number,
            message=message,
            notification_type=notification_type,
            scheduled_at=timezone.now()
        )

        if not self.twilio_client:
            logger.warning("Twilio client not configured, simulating SMS send")
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.twilio_sid = 'simulated_' + str(notification.id)[:8]
            notification.save(update_fields=['status', 'sent_at', 'twilio_sid'])
            logger.info(f"Simulated SMS sent to {phone_number}: {message}")
            return True

        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.twilio_sid = message_obj.sid
            notification.save(update_fields=['status', 'sent_at'])
            logger.info(f"SMS sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"SMS send failed to {phone_number}: {e}")
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save(update_fields=['status', 'error_message'])
            return False

    def send_medication_reminder(self, prescription, scheduled_datetime):
        """Send a medication reminder SMS."""
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

        return self.send_sms_notification(
            phone_number=prescription.patient.phone_number,
            message=body,
            notification_type='medication_reminder',
            recipient=prescription.patient
        )

    def send_missed_medication_alert(self, prescription, scheduled_datetime):
        """Send a missed medication alert SMS."""
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

        return self.send_sms_notification(
            phone_number=prescription.patient.phone_number,
            message=body,
            notification_type='missed_medication',
            recipient=prescription.patient
        )

    def send_manual_notification(self, patient, message):
        """Send a manual notification SMS."""
        return self.send_sms_notification(
            phone_number=patient.phone_number,
            message=message,
            notification_type='general',
            recipient=patient
        )
