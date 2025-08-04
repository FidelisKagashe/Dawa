from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('patient', 'Patient'),  # Active users (sick people)
        ('admin', 'Hospital Staff'),  # Admins who manage patients
        ('superuser', 'Hospital IT'),  # IT superuser who manages everything
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    medical_record_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.medical_record_number and self.user_type == 'patient':
            # Generate unique medical record number
            import uuid
            self.medical_record_number = f"MRN{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"
    
    @property
    def is_patient(self):
        return self.user_type == 'patient'
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'
    
    @property
    def is_hospital_it(self):
        return self.user_type == 'superuser' or self.is_superuser
    
    @property
    def can_manage_patients(self):
        return self.is_admin or self.is_hospital_it
    
    @property
    def can_manage_staff(self):
        return self.is_hospital_it

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    allergies = models.TextField(blank=True, help_text="List any known allergies")
    medical_conditions = models.TextField(blank=True, help_text="Current medical conditions")
    insurance_number = models.CharField(max_length=50, blank=True)
    attending_physician = models.CharField(max_length=100, blank=True)
    admission_date = models.DateTimeField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"