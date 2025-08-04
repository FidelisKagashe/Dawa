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
        ]
        
        for notif_type, name, template in templates_data:
            if not NotificationTemplate.objects.filter(name=name).exists():
                NotificationTemplate.objects.create(
                    name=name,
                    notification_type=notif_type,
                    template=template
                )
                self.stdout.write(f'Created notification template: {name}')
        
        self.stdout.write(self.style.SUCCESS('Hospital system initialized successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('Hospital IT: username=hospital_it, password=it123')
        self.stdout.write('Admin: username=admin, password=admin123')
        self.stdout.write('Patient: username=patient1, password=patient123')

if __name__ == '__main__':
    command = Command()
    command.handle()