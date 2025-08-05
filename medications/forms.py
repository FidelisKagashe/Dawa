from django import forms
from django.contrib.auth import get_user_model
from .models import Prescription, Medication, MedicationIntake, DailyMedicationSchedule

User = get_user_model()

class PrescriptionForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='patient', is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    medication = forms.ModelChoiceField(
        queryset=Medication.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Prescription
        fields = ['patient', 'medication', 'prescribing_physician', 'dosage', 
                 'frequency', 'start_date', 'end_date', 'special_instructions', 'priority']
        widgets = {
            'prescribing_physician': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg, 2 tablets'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }

class MedicationIntakeForm(forms.ModelForm):
    class Meta:
        model = MedicationIntake
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any notes about this intake...'})
        }

class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ['name', 'generic_name', 'medication_type', 'description', 'side_effects', 'contraindications']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'generic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'medication_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contraindications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UserCreationByAdminForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 
                 'date_of_birth', 'user_type', 'emergency_contact', 'emergency_phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class DailyScheduleConfirmForm(forms.ModelForm):
    class Meta:
        model = DailyMedicationSchedule
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any notes about taking this medication...'})
        }