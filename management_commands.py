#!/usr/bin/env python
"""
Custom management commands for the Hospital Medicine Management System
Run these commands using: python manage.py <command_name>
"""

import os
import sys
import django
from django.core.management.base import BaseCommand

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from medications.models import Medication, Prescription, MedicationSchedule, MedicationIntake
from notifications.models import NotificationTemplate
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize the hospital system with sample data'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing Hospital Medicine Management System...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@hospital.com',
                password='admin123',
                first_name='Hospital',
                last_name='Administrator',
                user_type='admin',
                phone_number='+1234567890'
            )
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create Hospital IT superuser
        if not User.objects.filter(username='hospital_it').exists():
            it_user = User.objects.create_user(
                username='hospital_it',
                email='it@hospital.com',
                password='it123',
                first_name='Hospital',
                last_name='IT Manager',
                user_type='superuser',
                phone_number='+1234567891'
            )
            it_user.is_staff = True
            it_user.is_superuser = True
            it_user.save()
            self.stdout.write(self.style.SUCCESS('Created Hospital IT superuser'))
        
        # Create sample patient
        if not User.objects.filter(username='patient1').exists():
            patient = User.objects.create_user(
                username='patient1',
                email='patient@example.com',
                password='patient123',
                first_name='John',
                last_name='Doe',
                user_type='patient',
                phone_number='+1987654321',
                date_of_birth='1980-01-01'
            )
            self.stdout.write(self.style.SUCCESS('Created sample patient'))
        
        # Create sample medications
        medications_data = [
            ('Aspirin', 'Acetylsalicylic acid', 'tablet', 'Pain reliever and anti-inflammatory'),
            ('Lisinopril', 'Lisinopril', 'tablet', 'ACE inhibitor for blood pressure'),
            ('Metformin', 'Metformin HCl', 'tablet', 'Diabetes medication'),
            ('Albuterol', 'Albuterol sulfate', 'inhaler', 'Bronchodilator for asthma'),
            ('Amoxicillin', 'Amoxicillin', 'capsule', 'Antibiotic for bacterial infections'),
            ('Ibuprofen', 'Ibuprofen', 'tablet', 'Anti-inflammatory pain reliever'),
        ]
        
        for name, generic, med_type, description in medications_data:
            if not Medication.objects.filter(name=name).exists():
                Medication.objects.create(
                    name=name,
                    generic_name=generic,
                    medication_type=med_type,
                    description=description
                )
                self.stdout.write(f'Created medication: {name}')
        
        # Create notification templates
        templates_data = [
            ('medication_reminder', 'Medication Reminder', 
             'Hi {patient_name}, time to take your {medication_name} ({dosage}). Scheduled for {time}.'),
            ('missed_medication', 'Missed Medication Alert', 
             'Alert: You missed your {medication_name} scheduled for {time}. Please take it as soon as possible.'),
            ('treatment_complete', 'Treatment Complete', 
             'Congratulations {patient_name}! You have completed your treatment course for {medication_name}.'),
            ('general', 'General Notification',
             'Hello {patient_name}, this is a message from your healthcare provider: {message}'),
        ]
        
        for notif_type, name, template in templates_data:
            if not NotificationTemplate.objects.filter(name=name).exists():
                NotificationTemplate.objects.create(
                    name=name,
                    notification_type=notif_type,
                    template=template
                )
                self.stdout.write(f'Created notification template: {name}')
        
        # Create sample daily schedules for existing prescriptions
        from medications.models import DailyMedicationSchedule
        from datetime import date, timedelta
        
        today = date.today()
        for i in range(7):  # Create schedules for next 7 days
            schedule_date = today + timedelta(days=i)
            
            # Get all active prescriptions
            active_prescriptions = Prescription.objects.filter(is_active=True)
            
            for prescription in active_prescriptions:
                # Create schedules based on frequency
                frequency_times = {
                    'once_daily': ['09:00'],
                    'twice_daily': ['09:00', '21:00'],
                    'three_times_daily': ['08:00', '14:00', '20:00'],
                    'four_times_daily': ['08:00', '12:00', '16:00', '20:00'],
                }
                
                times = frequency_times.get(prescription.frequency, ['09:00'])
                
                for time_str in times:
                    time_obj = timezone.datetime.strptime(time_str, '%H:%M').time()
                    
                    # Check if schedule already exists
                    if not DailyMedicationSchedule.objects.filter(
                        prescription=prescription,
                        date=schedule_date,
                        time_slot=time_obj
                    ).exists():
                        DailyMedicationSchedule.objects.create(
                            prescription=prescription,
                            date=schedule_date,
                            time_slot=time_obj
                        )
        
        self.stdout.write(self.style.SUCCESS('Hospital system initialized successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('Hospital IT: username=hospital_it, password=it123')
        self.stdout.write('Admin: username=admin, password=admin123')
        self.stdout.write('Patient: username=patient1, password=patient123')
        self.stdout.write('')
        self.stdout.write('Note: SMS notifications are simulated if Twilio is not configured.')
        self.stdout.write('Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env for real SMS.')

if __name__ == '__main__':
    command = Command()
    command.handle()