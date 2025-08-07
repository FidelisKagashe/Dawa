from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class EmailNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('medication_reminder', 'Medication Reminder'),
        ('missed_medication', 'Missed Medication'),
        ('treatment_complete', 'Treatment Complete'),
        ('emergency_alert', 'Emergency Alert'),
        ('general', 'General Notification'),
        ('feedback_request', 'Feedback Request'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_notifications')
    email_address = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    html_message = models.TextField(blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']

class SMSNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('medication_reminder', 'Medication Reminder'),
        ('missed_medication', 'Missed Medication'),
        ('treatment_complete', 'Treatment Complete'),
        ('emergency_alert', 'Emergency Alert'),
        ('general', 'General Notification'),
        ('feedback_request', 'Feedback Request'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    phone_number = models.CharField(max_length=17)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    twilio_sid = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=20, choices=SMSNotification.NOTIFICATION_TYPES)
    template = models.TextField(help_text="Use {patient_name}, {medication_name}, {time} as placeholders")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"
    
    class Meta:
        ordering = ['name']