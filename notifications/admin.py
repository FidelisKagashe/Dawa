from django.contrib import admin
from .models import SMSNotification, NotificationTemplate

@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'status', 'scheduled_at', 'sent_at')
    list_filter = ('notification_type', 'status', 'scheduled_at')
    search_fields = ('recipient__username', 'recipient__first_name', 'recipient__last_name', 'phone_number')
    readonly_fields = ('id', 'twilio_sid', 'sent_at', 'created_at')
    raw_id_fields = ('recipient',)

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'is_active', 'created_at')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('name', 'template')