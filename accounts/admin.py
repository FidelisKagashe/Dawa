from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PatientProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'date_of_birth', 'emergency_contact', 
                      'emergency_phone', 'medical_record_number')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'date_of_birth', 'emergency_contact', 
                      'emergency_phone')
        }),
    )

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'attending_physician', 'admission_date', 'is_active')
    list_filter = ('is_active', 'admission_date', 'discharge_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'attending_physician')
    raw_id_fields = ('user',)