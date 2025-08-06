from django.contrib import admin
from .models import Medication, Prescription, MedicationSchedule, MedicationIntake, DailyMedicationSchedule

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'medication_type', 'created_at')
    list_filter = ('medication_type', 'created_at')
    search_fields = ('name', 'generic_name')
    readonly_fields = ('created_at',)

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('medication', 'patient', 'prescribing_physician', 'frequency', 'priority', 'is_active')
    list_filter = ('frequency', 'priority', 'is_active', 'start_date')
    search_fields = ('medication__name', 'patient__username', 'patient__first_name', 'patient__last_name')
    raw_id_fields = ('patient', 'medication', 'created_by')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(MedicationSchedule)
class MedicationScheduleAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'scheduled_time', 'is_active')
    list_filter = ('is_active', 'scheduled_time')
    raw_id_fields = ('prescription',)

@admin.register(DailyMedicationSchedule)
class DailyMedicationScheduleAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'date', 'time_slot', 'is_taken', 'taken_at')
    list_filter = ('is_taken', 'date', 'created_at')
    search_fields = ('prescription__medication__name', 'prescription__patient__username')
    readonly_fields = ('created_at',)
    raw_id_fields = ('prescription',)
@admin.register(MedicationIntake)
class MedicationIntakeAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'scheduled_datetime', 'actual_datetime', 'status')
    list_filter = ('status', 'scheduled_datetime', 'created_at')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('prescription',)