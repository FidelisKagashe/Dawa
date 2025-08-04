from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ProgressReport(models.Model):
    REPORT_TYPES = [
        ('treatment_complete', 'Treatment Complete'),
        ('weekly_summary', 'Weekly Summary'),
        ('monthly_summary', 'Monthly Summary'),
        ('discharge_summary', 'Discharge Summary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    compliance_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_medications = models.IntegerField(default=0)
    taken_medications = models.IntegerField(default=0)
    missed_medications = models.IntegerField(default=0)
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    pdf_file = models.FileField(upload_to='reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.patient.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']