from django.contrib import admin
from .models import ProgressReport

@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'patient', 'report_type', 'compliance_rate', 'created_at')
    list_filter = ('report_type', 'created_at', 'report_period_start')
    search_fields = ('title', 'patient__username', 'patient__first_name', 'patient__last_name')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('patient', 'generated_by')