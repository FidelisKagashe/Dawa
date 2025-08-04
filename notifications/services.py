# notifications/services.py

import logging
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from .models import SMSNotification, NotificationTemplate

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self._client = None
        self.from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

    @property
    def client(self):
        # Lazy-init Twilio client only if credentials are present
        if self._client is None:
            sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            if not sid or not token:
                logger.warning("Twilio credentials missing; running in simulation mode.")
                return None
            self._client = Client(sid, token)
        return self._client

    def send_sms(self, to_number, message, notification_type='general', recipient=None):
        """Send SMS via Twilio (or simulate) and log it to the DB."""
        # Create the notification record
        notification = SMSNotification.objects.create(
            recipient=recipient,
            phone_number=to_number,
            message=message,
            notification_type=notification_type,
            scheduled_at=timezone.now()
        )

        # Simulation mode if no client
        if self.client is None:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at'])
            return True

        # Actual send
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.twilio_sid = msg.sid
            notification.save(update_fields=['status', 'sent_at', 'twilio_sid'])
            logger.info(f"SMS sent to {to_number}, SID={msg.sid}")
            return True

        except Exception as e:
            logger.error(f"SMS send failed to {to_number}: {e}")
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

        return self.send_sms(
            to_number=prescription.patient.phone_number,
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

        return self.send_sms(
            to_number=prescription.patient.phone_number,
            message=body,
            notification_type='missed_medication',
            recipient=prescription.patient
        )
