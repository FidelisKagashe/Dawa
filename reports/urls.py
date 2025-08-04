from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='report_list'),
    path('generate/<int:patient_id>/', views.generate_patient_report, name='generate_report'),
    path('download/<uuid:report_id>/', views.download_report_pdf, name='download_pdf'),
]