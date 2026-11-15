from django import forms
from django.forms import inlineformset_factory
from .models import (
    Department, Doctor, Patient, Appointment,
    MedicalRecord, PatientVital, Medicine, Prescription, Invoice
)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Cardiology'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Department details'}),
        }


class DoctorForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    DAY_CHOICES = (
        ('Mon', 'Mon'), ('Tue', 'Tue'), ('Wed', 'Wed'),
        ('Thu', 'Thu'), ('Fri', 'Fri'), ('Sat', 'Sat'), ('Sun', 'Sun'),
    )
    days_selection = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    class Meta:
        model = Doctor
        fields = [
            'department', 'specialization', 'phone_number',
            'consultation_fee', 'available_time_start', 'available_time_end'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Cardiologist'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '50'}),
            'available_time_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'available_time_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['days_selection'].initial = self.instance.get_available_days_list()

    def save(self, commit=True):
        doctor = super().save(commit=False)
        selected_days = self.cleaned_data.get('days_selection', [])
        doctor.available_days = ",".join(selected_days)
        if commit:
            doctor.save()
            doctor.user.first_name = self.cleaned_data['first_name']
            doctor.user.last_name = self.cleaned_data['last_name']
            doctor.user.email = self.cleaned_data['email']
            doctor.user.save()
        return doctor


class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select select2'}),
            'doctor': forms.Select(attrs={'class': 'form-select select2', 'id': 'id_doctor_select'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_appointment_date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'id_appointment_time'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Primary complaint / symptoms'}),
        }


class PatientSelfBookingForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department_filter'})
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor_select'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_appointment_date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'id_appointment_time'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your symptoms or reason for visit'}),
        }


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['symptoms', 'diagnosis', 'notes']
        widgets = {
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observed symptoms / patient reported complaint'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Clinical diagnosis & condition'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Advice, lifestyle guidance, or follow-up instructions'}),
        }


class PatientVitalForm(forms.ModelForm):
    class Meta:
        model = PatientVital
        fields = ['blood_pressure', 'pulse_rate', 'temperature', 'weight', 'oxygen_saturation']
        widgets = {
            'blood_pressure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '120/80 mmHg'}),
            'pulse_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '72 bpm'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '98.6 °F'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '70.0 kg'}),
            'oxygen_saturation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '98 %'}),
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['medicine', 'dosage', 'frequency', 'duration_days', 'instructions']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 500mg or 10ml'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1-0-1 or 2x daily'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'instructions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. After meals'}),
        }


PrescriptionFormSet = inlineformset_factory(
    MedicalRecord,
    Prescription,
    form=PrescriptionForm,
    extra=1,
    can_delete=True
)


class InvoicePaymentForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['status', 'payment_method']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }

