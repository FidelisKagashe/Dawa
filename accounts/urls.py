from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.PatientRegistrationView.as_view(), name='register'),
    path('staff/register/', views.StaffRegistrationView.as_view(), name='staff_register'),
]