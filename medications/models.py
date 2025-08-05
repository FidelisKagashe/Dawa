from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

User = get_user_model()

class Medication(models.Model):
    MEDICATION_TYPES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('liquid', 'Liquid'),
        ('injection', 'Injection'),
        ('topical', 'Topical'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    medication_type = models.CharField(max_length=20, choices=MEDICATION_TYPES, default='tablet')
    description = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_medication_type_display()})"
    
    class Meta:
        ordering = ['name']

class Prescription(models.Model):
    FREQUENCY_CHOICES = [
        ('once_daily', 'Once Daily'),
        ('twice_daily', 'Twice Daily'),
        ('three_times_daily', 'Three Times Daily'),
        ('four_times_daily', 'Four Times Daily'),
        ('every_4_hours', 'Every 4 Hours'),
        ('every_6_hours', 'Every 6 Hours'),
        ('every_8_hours', 'Every 8 Hours'),
        ('every_12_hours', 'Every 12 Hours'),
        ('as_needed', 'As Needed'),
        ('custom', 'Custom Schedule'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    prescribing_physician = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100, help_text="e.g., 500mg, 2 tablets")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    special_instructions = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescribed_medications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.medication.name} for {self.patient.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']

class MedicationSchedule(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='schedules')
    scheduled_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.prescription.medication.name} at {self.scheduled_time}"
    
    class Meta:
        ordering = ['scheduled_time']

class DailyMedicationSchedule(models.Model):
    """Daily medication schedule for a specific prescription"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='daily_schedules')
    date = models.DateField()
    time_slot = models.TimeField()
    is_taken = models.BooleanField(default=False)
    taken_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.prescription.medication.name} - {self.date} at {self.time_slot}"
    
    @property
    def is_overdue(self):
        if not self.is_taken:
            scheduled_datetime = timezone.datetime.combine(self.date, self.time_slot)
            return timezone.now() > timezone.make_aware(scheduled_datetime)
        return False
    
    class Meta:
        ordering = ['date', 'time_slot']
        unique_together = ['prescription', 'date', 'time_slot']
class MedicationIntake(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('taken', 'Taken'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='intakes')
    scheduled_datetime = models.DateTimeField()
    actual_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.prescription.medication.name} - {self.scheduled_datetime} ({self.status})"
    
    @property
    def is_overdue(self):
        if self.status == 'pending' and timezone.now() > self.scheduled_datetime:
            return True
        return False
    
    class Meta:
        ordering = ['-scheduled_datetime']
        unique_together = ['prescription', 'scheduled_datetime']