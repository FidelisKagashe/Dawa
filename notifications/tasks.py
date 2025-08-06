from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from medications.models import MedicationIntake, Prescription, DailyMedicationSchedule
from .services import NotificationService
import logging

logger = logging.getLogger(__name__)

notification_service = NotificationService()
@shared_task
def send_medication_reminders():
    """Send SMS reminders for upcoming medications"""
    now = timezone.now()
    reminder_time = now + timedelta(minutes=15)  # 15 minutes before
    
    # Get daily schedules for today that haven't been taken
    today = now.date()
    current_time = now.time()
    reminder_time_obj = (now + timedelta(minutes=15)).time()
    
    upcoming_schedules = DailyMedicationSchedule.objects.filter(
        date=today,
        is_taken=False,
        time_slot__range=(current_time, reminder_time_obj)
    )
    
    for schedule in upcoming_schedules:
        if schedule.prescription.patient.phone_number:
            scheduled_datetime = timezone.datetime.combine(schedule.date, schedule.time_slot)
            notification_service.send_medication_reminder(
                schedule.prescription,
                scheduled_datetime
            )
    
    logger.info(f"Sent {upcoming_schedules.count()} medication reminders")

@shared_task
def check_missed_medications():
    """Check for missed medications and send alerts"""
    now = timezone.now()
    today = now.date()
    current_time = now.time()
    grace_period_time = (now - timedelta(hours=1)).time()
    
    missed_schedules = DailyMedicationSchedule.objects.filter(
        date=today,
        is_taken=False,
        time_slot__lt=grace_period_time
    )
    
    for schedule in missed_schedules:
        # Send alert if critical or high priority
        if schedule.prescription.priority in ['critical', 'high']:
            if schedule.prescription.patient.phone_number:
                scheduled_datetime = timezone.datetime.combine(schedule.date, schedule.time_slot)
                notification_service.send_missed_medication_alert(
                    schedule.prescription,
                    scheduled_datetime
                )
        
    logger.info(f"Processed {missed_schedules.count()} missed medications")

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