from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date, time


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Doctor(models.Model):
    DAYS_OF_WEEK = [
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='doctors'
    )
    specialization = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    # Stored as comma-separated days, e.g. "Mon,Tue,Wed,Thu,Fri"
    available_days = models.CharField(
        max_length=100,
        default='Mon,Tue,Wed,Thu,Fri',
        help_text='Comma-separated short day names: Mon,Tue,Wed,Thu,Fri,Sat,Sun'
    )
    available_time_start = models.TimeField(default=time(9, 0))
    available_time_end = models.TimeField(default=time(17, 0))

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        dept_name = self.department.name if self.department else 'General'
        return f"Dr. {full_name} ({self.specialization} - {dept_name})"

    def get_available_days_list(self):
        if not self.available_days:
            return []
        return [d.strip() for d in self.available_days.split(',') if d.strip()]

    def is_available_on_date(self, target_date):
        day_abbr = target_date.strftime('%a')  # 'Mon', 'Tue', etc.
        return day_abbr in self.get_available_days_list()


class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} (ID: PAT-{self.id:04d})"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(help_text='Chief complaint / reason for visit')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                condition=~models.Q(status='cancelled'),
                name='unique_active_doctor_appointment_slot'
            )
        ]

    def __str__(self):
        return f"Appt #{self.id}: {self.patient} with {self.doctor} on {self.appointment_date} at {self.appointment_time.strftime('%H:%M')}"

    def clean(self):
        super().clean()
        if not self.doctor_id or not self.appointment_date or not self.appointment_time:
            return

        # 1. Date cannot be in the past (for new pending/confirmed appointments)
        if self.pk is None and self.appointment_date < timezone.now().date():
            raise ValidationError({'appointment_date': 'Appointment date cannot be in the past.'})

        # 2. Check if doctor is available on that day of week
        if not self.doctor.is_available_on_date(self.appointment_date):
            available = ", ".join(self.doctor.get_available_days_list())
            raise ValidationError({
                'appointment_date': f"Dr. {self.doctor.user.get_full_name()} is only available on: {available}."
            })

        # 3. Check doctor operating hours
        if not (self.doctor.available_time_start <= self.appointment_time < self.doctor.available_time_end):
            start_str = self.doctor.available_time_start.strftime('%H:%M')
            end_str = self.doctor.available_time_end.strftime('%H:%M')
            raise ValidationError({
                'appointment_time': f"Appointment time must be between {start_str} and {end_str}."
            })

        # 4. Check double-booking conflicts for doctor
        conflict_query = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time
        ).exclude(status='cancelled')

        if self.pk:
            conflict_query = conflict_query.exclude(pk=self.pk)

        if conflict_query.exists():
            raise ValidationError({
                'appointment_time': f"Dr. {self.doctor.user.get_full_name()} already has an appointment booked at this date and time."
            })


class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='medical_record'
    )
    symptoms = models.TextField(blank=True, null=True)
    diagnosis = models.TextField()
    notes = models.TextField(blank=True, null=True, help_text="Doctor's clinical observations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Record #{self.id} for {self.patient} ({self.created_at.strftime('%Y-%m-%d')})"


class PatientVital(models.Model):
    medical_record = models.OneToOneField(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='vitals'
    )
    blood_pressure = models.CharField(max_length=20, blank=True, null=True, help_text="e.g. 120/80 mmHg")
    pulse_rate = models.PositiveIntegerField(blank=True, null=True, help_text="Heart rate (bpm)")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, help_text="Body Temp (°F)")
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Weight (kg)")
    oxygen_saturation = models.PositiveIntegerField(blank=True, null=True, help_text="SpO2 (%)")

    def __str__(self):
        return f"Vitals for Record #{self.medical_record_id}"


class Medicine(models.Model):
    DOSAGE_FORMS = (
        ('tablet', 'Tablet'),
        ('syrup', 'Syrup'),
        ('capsule', 'Capsule'),
        ('injection', 'Injection'),
        ('ointment', 'Ointment'),
        ('drops', 'Drops'),
    )

    name = models.CharField(max_length=150, unique=True)
    dosage_form = models.CharField(max_length=50, choices=DOSAGE_FORMS, default='tablet')
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    stock_quantity = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_dosage_form_display()})"


class Prescription(models.Model):
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    dosage = models.CharField(max_length=100, help_text="e.g. 500mg, 10ml")
    frequency = models.CharField(max_length=100, help_text="e.g. 2x daily, 1-0-1 after meals")
    duration_days = models.PositiveIntegerField(default=5)
    instructions = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. Take after meals")

    def __str__(self):
        return f"{self.medicine.name} - {self.dosage} ({self.frequency} for {self.duration_days} days)"


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI / Online Transfer'),
        ('insurance', 'Health Insurance'),
    )

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Invoice #{self.id:05d} - {self.patient} - ₹{self.total_amount} ({self.get_status_display()})"

    def calculate_total(self):
        total = sum(item.amount for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.description}: ₹{self.amount}"
