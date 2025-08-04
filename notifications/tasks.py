from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from medications.models import MedicationIntake, Prescription
from .services import sms_service
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_medication_reminders():
    """Send SMS reminders for upcoming medications"""
    now = timezone.now()
    reminder_time = now + timedelta(minutes=15)  # 15 minutes before
    
    # Get pending medications in the next 15 minutes
    upcoming_intakes = MedicationIntake.objects.filter(
        status='pending',
        scheduled_datetime__range=(now, reminder_time)
    )
    
    for intake in upcoming_intakes:
        if intake.prescription.patient.phone_number:
            sms_service.send_medication_reminder(
                intake.prescription,
                intake.scheduled_datetime
            )
    
    logger.info(f"Sent {upcoming_intakes.count()} medication reminders")

@shared_task
def check_missed_medications():
    """Check for missed medications and send alerts"""
    now = timezone.now()
    grace_period = now - timedelta(hours=1)  # 1 hour grace period
    
    missed_intakes = MedicationIntake.objects.filter(
        status='pending',
        scheduled_datetime__lt=grace_period
    )
    
    for intake in missed_intakes:
        # Mark as missed
        intake.status = 'missed'
        intake.save()
        
        # Send alert if critical or high priority
        if intake.prescription.priority in ['critical', 'high']:
            if intake.prescription.patient.phone_number:
                sms_service.send_missed_medication_alert(
                    intake.prescription,
                    intake.scheduled_datetime
                )
    
    logger.info(f"Marked {missed_intakes.count()} medications as missed")

@shared_task
def generate_daily_medication_schedule():
    """Generate medication intake records for the next day"""
    from medications.models import MedicationSchedule
    
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    active_prescriptions = Prescription.objects.filter(
        is_active=True,
        start_date__lte=tomorrow
    )
    
    for prescription in active_prescriptions:
        # Skip if prescription has ended
        if prescription.end_date and prescription.end_date < tomorrow:
            continue
        
        # Create intake records for each scheduled time
        for schedule in prescription.schedules.filter(is_active=True):
            scheduled_datetime = timezone.datetime.combine(
                tomorrow,
                schedule.scheduled_time,
                tzinfo=timezone.get_current_timezone()
            )
            
            # Check if intake record already exists
            if not MedicationIntake.objects.filter(
                prescription=prescription,
                scheduled_datetime=scheduled_datetime
            ).exists():
                MedicationIntake.objects.create(
                    prescription=prescription,
                    scheduled_datetime=scheduled_datetime
                )
    
    logger.info(f"Generated medication schedule for {tomorrow}")