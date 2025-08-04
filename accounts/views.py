from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import User, PatientProfile
from .forms import PatientRegistrationForm, StaffRegistrationForm, CustomLoginForm

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if user.can_manage_patients:
            return reverse_lazy('medications:admin_dashboard')
        return reverse_lazy('medications:dashboard')

class PatientRegistrationView(SuccessMessageMixin, CreateView):
    model = User
    form_class = PatientRegistrationForm
    template_name = 'accounts/register.html'
    success_message = "Your account has been created successfully. You can now login."
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user.user_type = 'patient'
        user.save()
        
        # Create patient profile
        PatientProfile.objects.create(user=user)
        
        messages.success(self.request, "Registration successful! Please login to continue.")
        return response

class StaffRegistrationView(SuccessMessageMixin, CreateView):
    model = User
    form_class = StaffRegistrationForm
    template_name = 'accounts/staff_register.html'
    success_message = "Staff account has been created successfully."
    success_url = reverse_lazy('medications:admin_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.can_manage_staff:
            messages.error(request, "Access denied. Only Hospital IT can create staff accounts.")
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user.user_type = 'admin'
        user.save()
        
        messages.success(self.request, f"Staff account created for {user.get_full_name()}")
        return response
class CustomLogoutView(LogoutView):
    next_page = 'accounts:login'
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been successfully logged out.")
        return super().dispatch(request, *args, **kwargs)