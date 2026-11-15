from django.contrib import admin
from .models import (
    Department, Doctor, Patient, Appointment,
    MedicalRecord, PatientVital, Medicine, Prescription,
    Invoice, InvoiceItem
)


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1
    autocomplete_fields = ['medicine']


class PatientVitalInline(admin.StackedInline):
    model = PatientVital
    can_delete = False
    max_num = 1


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'doctor_count', 'created_at')
    search_fields = ('name', 'description')

    def doctor_count(self, obj):
        return obj.doctors.count()
    doctor_count.short_description = 'Doctors'


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'department', 'specialization', 'phone_number', 'consultation_fee', 'available_days')
    list_filter = ('department', 'available_days')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'specialization', 'phone_number')

    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name() or obj.user.username}"
    get_full_name.short_description = 'Doctor'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'gender', 'blood_group', 'phone_number', 'date_of_birth', 'created_at')
    list_filter = ('gender', 'blood_group', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'phone_number', 'address')

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Patient Name'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'doctor__department')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name', 'reason')
    date_hierarchy = 'appointment_date'


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'get_doctor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'diagnosis', 'symptoms')
    inlines = [PatientVitalInline, PrescriptionInline]

    def get_doctor(self, obj):
        return obj.appointment.doctor
    get_doctor.short_description = 'Consulting Doctor'


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'dosage_form', 'unit_price', 'stock_quantity')
    list_filter = ('dosage_form',)
    search_fields = ('name',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'total_amount', 'status', 'payment_method', 'issued_at', 'paid_at')
    list_filter = ('status', 'payment_method', 'issued_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'id')
    inlines = [InvoiceItemInline]
