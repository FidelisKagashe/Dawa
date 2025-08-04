from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('send-manual/', views.send_manual_notification, name='send_manual'),
    path('history/', views.NotificationHistoryView.as_view(), name='history'),
]