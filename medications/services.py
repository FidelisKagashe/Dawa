from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Q
from .models import Prescription, DailyMedicationSchedule, MedicationFeedback
from notifications.services import NotificationService
import logging

logger = logging.getLogger(__name__)

class MedicationSchedulingService:
    """Service for handling medication scheduling and automatic notifications"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def generate_schedules_for_date(self, date=None):
        """Generate medication schedules for all active prescriptions for a specific date"""
        if date is None:
            date = timezone.now().date()
        
        active_prescriptions = Prescription.objects.filter(
            is_active=True,
            start_date__lte=date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date)
        )
        
        generated_count = 0
        for prescription in active_prescriptions:
            try:
                schedules = prescription.generate_daily_schedules(date)
                generated_count += len(schedules)
                logger.info(f"Generated {len(schedules)} schedules for {prescription}")
            except Exception as e:
                logger.error(f"Error generating schedules for {prescription}: {e}")
        
        logger.info(f"Generated {generated_count} total schedules for {date}")
        return generated_count
    
    def send_due_medication_reminders(self):
        """Send email reminders for medications that are due soon"""
        now = timezone.now()
        current_date = now.date()
        
        # Get schedules that are due within 15 minutes and haven't been sent email yet
        due_schedules = DailyMedicationSchedule.objects.filter(
            date=current_date,
            is_taken=False,
            email_sent=False
        )
        
        sent_count = 0
        for schedule in due_schedules:
            try:
                scheduled_datetime = timezone.make_aware(
                    datetime.combine(schedule.date, schedule.time_slot)
                )
                
                # Check if it's time to send reminder (15 minutes before)
                time_until_dose = scheduled_datetime - now
                
                if timedelta(0) <= time_until_dose <= timedelta(minutes=15):
                    # Send email reminder
                    success = self.notification_service.send_medication_reminder_email(
                        schedule.prescription,
                        scheduled_datetime
                    )
                    
                    if success:
                        schedule.email_sent = True
                        schedule.email_sent_at = now
                        schedule.save(update_fields=['email_sent', 'email_sent_at'])
                        sent_count += 1
                        logger.info(f"Sent reminder for {schedule}")
                
            except Exception as e:
                logger.error(f"Error sending reminder for {schedule}: {e}")
        
        logger.info(f"Sent {sent_count} medication reminders")
        return sent_count
    
    def send_overdue_medication_alerts(self):
        """Send alerts for overdue medications"""
        now = timezone.now()
        current_date = now.date()
        
        # Get schedules that are overdue (30 minutes past scheduled time)
        overdue_schedules = DailyMedicationSchedule.objects.filter(
            date=current_date,
            is_taken=False
        )
        
        sent_count = 0
        for schedule in overdue_schedules:
            try:
                scheduled_datetime = timezone.make_aware(
                    datetime.combine(schedule.date, schedule.time_slot)
                )
                
                # Check if it's overdue (30 minutes past)
                time_since_due = now - scheduled_datetime
                
                if time_since_due > timedelta(minutes=30):
                    # Only send alert for high priority medications
                    if schedule.prescription.priority in ['high', 'critical']:
                        success = self.notification_service.send_missed_medication_alert_email(
                            schedule.prescription,
                            scheduled_datetime
                        )
                        
                        if success:
                            sent_count += 1
                            logger.info(f"Sent overdue alert for {schedule}")
                
            except Exception as e:
                logger.error(f"Error sending overdue alert for {schedule}: {e}")
        
        logger.info(f"Sent {sent_count} overdue medication alerts")
        return sent_count
    
    def mark_medication_taken(self, schedule_id, notes=""):
        """Mark a medication as taken"""
        try:
            schedule = DailyMedicationSchedule.objects.get(id=schedule_id)
            schedule.is_taken = True
            schedule.taken_at = timezone.now()
            if notes:
                schedule.notes = notes
            schedule.save()
            
            # Send confirmation email
            self.notification_service.send_medication_confirmation_email(
                schedule.prescription,
                schedule.taken_at
            )
            
            logger.info(f"Marked medication as taken: {schedule}")
            return True
            
        except DailyMedicationSchedule.DoesNotExist:
            logger.error(f"Schedule with id {schedule_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error marking medication as taken: {e}")
            return False
    
    def get_patient_today_schedule(self, patient):
        """Get today's medication schedule for a patient"""
        today = timezone.now().date()
        
        schedules = DailyMedicationSchedule.objects.filter(
            prescription__patient=patient,
            date=today
        ).select_related('prescription__medication').order_by('time_slot')
        
        return schedules
    
    def get_upcoming_medications(self, patient, hours_ahead=24):
        """Get upcoming medications for a patient"""
        now = timezone.now()
        end_time = now + timedelta(hours=hours_ahead)
        
        schedules = DailyMedicationSchedule.objects.filter(
            prescription__patient=patient,
            date__range=[now.date(), end_time.date()],
            is_taken=False
        ).select_related('prescription__medication').order_by('date', 'time_slot')
        
        upcoming = []
        for schedule in schedules:
            scheduled_datetime = timezone.make_aware(
                datetime.combine(schedule.date, schedule.time_slot)
            )
            if scheduled_datetime >= now:
                upcoming.append({
                    'schedule': schedule,
                    'datetime': scheduled_datetime,
                    'time_until': scheduled_datetime - now
                })
        
        return upcoming[:10]  # Return next 10 medications

# Initialize the service
medication_service = MedicationSchedulingService()