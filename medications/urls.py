from django.urls import path
from . import views

app_name = 'medications'

urlpatterns = [
    path('dashboard/', views.PatientDashboardView.as_view(), name='dashboard'),
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('prescription/create/', views.PrescriptionCreateView.as_view(), name='prescription_create'),
    path('intake/confirm/<uuid:intake_id>/', views.confirm_medication_intake, name='confirm_intake'),
    path('admin/patient/<int:pk>/', views.PatientDetailView.as_view(), name='patient_detail'),
    path('history/', views.MedicationHistoryView.as_view(), name='medication_history'),
]