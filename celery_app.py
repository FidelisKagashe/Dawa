import logging
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from twilio.rest import Client
from .models import SMSNotification, EmailNotification, NotificationTemplate

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
    
    def send_email_notification(self, email_address, subject, message, html_message=None, 
                              notification_type='general', recipient=None):
        """Send email notification and log it to the DB."""
        # Create the notification record
        notification = EmailNotification.objects.create(
            recipient=recipient,
            email_address=email_address,
            subject=subject,
            message=message,
            html_message=html_message or '',
            notification_type=notification_type,
    
    def send_email_notification(self, email_address, subject, message, html_message=None, 
                              notification_type='general', recipient=None):
        """Send email notification and log it to the DB."""
        # Create the notification record
        notification = EmailNotification.objects.create(
            recipient=recipient,
            email_address=email_address,
            subject=subject,
            message=message,
            html_message=html_message or '',
            notification_type=notification_type,
            scheduled_at=timezone.now()
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_address],
                html_message=html_message,
                fail_silently=False,
            )
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at'])
            logger.info(f"Email sent to {email_address}")
            return True
        except Exception as e:
            logger.error(f"Email send failed to {email_address}: {e}")
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save(update_fields=['status', 'error_message'])
            return False

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

    def send_medication_reminder_email(self, prescription, scheduled_datetime):
        """Send a medication reminder email."""
        tpl = NotificationTemplate.objects.filter(
            notification_type='medication_reminder', is_active=True
        ).first()

        if tpl:
            message = tpl.template.format(
                patient_name=prescription.patient.get_full_name(),
                medication_name=prescription.medication.name,
                dosage=prescription.dosage,
                time=scheduled_datetime.strftime('%I:%M %p')
            )
        else:
            message = (
                f"Habari {prescription.patient.get_full_name()},\n\n"
                f"Hii ni ukumbusho wa kutumia dawa yako:\n"
                f"Dawa: {prescription.medication.name}\n"
                f"Kipimo: {prescription.dosage}\n"
                f"Muda: {scheduled_datetime.strftime('%I:%M %p')}\n\n"
                f"Tafadhali tumia dawa yako kwa wakati na uthibitishe kupitia mfumo wetu.\n\n"
                f"Asante,\nTimu ya MedCare"
            )

        subject = f"Ukumbusho wa Dawa - {prescription.medication.name}"
        
        # Create HTML version
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563EB;">🏥 MedCare - Ukumbusho wa Dawa</h2>
                <p>Habari <strong>{prescription.patient.get_full_name()}</strong>,</p>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #059669; margin-top: 0;">Muda wa Dawa Umefika!</h3>
                    <p><strong>Dawa:</strong> {prescription.medication.name}</p>
                    <p><strong>Kipimo:</strong> {prescription.dosage}</p>
                    <p><strong>Muda:</strong> {scheduled_datetime.strftime('%I:%M %p')}</p>
                </div>
                <p>Tafadhali tumia dawa yako kwa wakati na uthibitishe kupitia mfumo wetu.</p>
                <p style="margin-top: 30px;">Asante,<br><strong>Timu ya MedCare</strong></p>
            </div>
        </body>
        </html>
        """

        return self.send_email_notification(
            email_address=prescription.patient.email,
            subject=subject,
            message=message,
            html_message=html_message,
            notification_type='medication_reminder',
            recipient=prescription.patient
        )

    def send_missed_medication_alert_email(self, prescription, scheduled_datetime):
        """Send a missed medication alert email."""
        subject = f"Onyo la Dawa - {prescription.medication.name}"
        
        message = (
            f"Habari {prescription.patient.get_full_name()},\n\n"
            f"Umesahau kutumia dawa yako:\n"
            f"Dawa: {prescription.medication.name}\n"
            f"Muda uliokuwa umepangwa: {scheduled_datetime.strftime('%I:%M %p')}\n\n"
            f"Tafadhali tumia dawa yako haraka iwezekanavyo na uthibitishe kupitia mfumo wetu.\n\n"
            f"Asante,\nTimu ya MedCare"
        )
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #DC2626;">⚠️ MedCare - Onyo la Dawa</h2>
                <p>Habari <strong>{prescription.patient.get_full_name()}</strong>,</p>
                <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #DC2626;">
                    <h3 style="color: #DC2626; margin-top: 0;">Umesahau Dawa Yako!</h3>
                    <p><strong>Dawa:</strong> {prescription.medication.name}</p>
                    <p><strong>Muda uliokuwa umepangwa:</strong> {scheduled_datetime.strftime('%I:%M %p')}</p>
                </div>
                <p>Tafadhali tumia dawa yako haraka iwezekanavyo na uthibitishe kupitia mfumo wetu.</p>
                <p style="margin-top: 30px;">Asante,<br><strong>Timu ya MedCare</strong></p>
            </div>
        </body>
        </html>
        """

        return self.send_email_notification(
            email_address=prescription.patient.email,
            subject=subject,
            message=message,
            html_message=html_message,
            notification_type='missed_medication',
            recipient=prescription.patient
        )

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

    def send_manual_notification(self, patient, message, use_email=True):
        """Send a manual notification SMS."""
        if use_email and patient.email:
            return self.send_email_notification(
                email_address=patient.email,
                subject="Ujumbe kutoka Hospitali",
                message=message,
                notification_type='general',
                recipient=patient
            )
        else:
            return self.send_sms_notification(
                phone_number=patient.phone_number,
                message=message,
                notification_type='general',
                recipient=patient
            )
