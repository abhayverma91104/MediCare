import json
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.decorators import (
    role_required, admin_required, doctor_required,
    receptionist_required, patient_required, staff_required
)
from .models import (
    Department, Doctor, Patient, Appointment,
    MedicalRecord, PatientVital, Medicine, Prescription,
    Invoice, InvoiceItem
)
from .forms import (
    DepartmentForm, DoctorForm, AppointmentBookingForm,
    PatientSelfBookingForm, MedicalRecordForm, PatientVitalForm,
    PrescriptionFormSet, InvoicePaymentForm
)
from accounts.forms import PatientRegistrationForm, StaffCreationForm

User = get_user_model()


# =====================================================================
# 1. PUBLIC VIEWS
# =====================================================================

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    departments = Department.objects.annotate(doc_count=Count('doctors')).all()[:6]
    doctors = Doctor.objects.select_related('user', 'department').all()[:6]
    stats = {
        'total_doctors': Doctor.objects.count(),
        'total_patients': Patient.objects.count(),
        'total_departments': Department.objects.count(),
        'total_consultations': Appointment.objects.filter(status='completed').count(),
    }
    return render(request, 'hospital/home.html', {
        'departments': departments,
        'doctors': doctors,
        'stats': stats,
    })


def doctor_directory(request):
    dept_id = request.GET.get('department')
    search_query = request.GET.get('q', '').strip()

    doctors = Doctor.objects.select_related('user', 'department').all()
    if dept_id:
        doctors = doctors.filter(department_id=dept_id)
    if search_query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )

    departments = Department.objects.all()
    return render(request, 'hospital/doctor_directory.html', {
        'doctors': doctors,
        'departments': departments,
        'selected_dept': dept_id,
        'search_query': search_query,
    })


# =====================================================================
# 2. ADMIN VIEWS
# =====================================================================

@admin_required
def admin_dashboard(request):
    today = timezone.now().date()
    total_doctors = Doctor.objects.count()
    total_patients = Patient.objects.count()
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    
    total_revenue = Invoice.objects.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    recent_appointments = Appointment.objects.select_related('patient__user', 'doctor__user', 'doctor__department')\
        .order_by('-created_at')[:8]
    recent_patients = Patient.objects.select_related('user').order_by('-created_at')[:5]

    return render(request, 'hospital/admin/dashboard.html', {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'total_revenue': total_revenue,
        'recent_appointments': recent_appointments,
        'recent_patients': recent_patients,
    })


@admin_required
def admin_doctor_list(request):
    doctors = Doctor.objects.select_related('user', 'department').all()
    return render(request, 'hospital/admin/doctor_list.html', {'doctors': doctors})


@admin_required
def admin_doctor_create(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        if not username or not password:
            messages.error(request, "Username and password are required for the new doctor account.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "A user with this username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
        elif form.is_valid():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='doctor'
            )
            doctor = form.save(commit=False)
            doctor.user = user
            doctor.save()
            messages.success(request, f"Dr. {user.get_full_name()} has been successfully added.")
            return redirect('admin_doctor_list')
    else:
        form = DoctorForm()

    return render(request, 'hospital/admin/doctor_form.html', {'form': form, 'title': 'Add New Doctor'})


@admin_required
def admin_doctor_edit(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dr. {doctor.user.get_full_name()} updated successfully.")
            return redirect('admin_doctor_list')
    else:
        form = DoctorForm(instance=doctor)

    return render(request, 'hospital/admin/doctor_form.html', {
        'form': form,
        'doctor': doctor,
        'title': f"Edit Dr. {doctor.user.get_full_name()}"
    })


@admin_required
def admin_doctor_delete(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        user = doctor.user
        doctor_name = user.get_full_name()
        user.delete()  # Cascade deletes doctor
        messages.success(request, f"Doctor {doctor_name} has been removed.")
        return redirect('admin_doctor_list')
    return render(request, 'hospital/admin/confirm_delete.html', {
        'object_name': f"Dr. {doctor.user.get_full_name()}",
        'cancel_url': 'admin_doctor_list'
    })


@admin_required
def admin_department_list(request):
    departments = Department.objects.annotate(doc_count=Count('doctors')).all()
    return render(request, 'hospital/admin/department_list.html', {'departments': departments})


@admin_required
def admin_department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' created.")
            return redirect('admin_department_list')
    else:
        form = DepartmentForm()
    return render(request, 'hospital/admin/department_form.html', {'form': form, 'title': 'Create Department'})


@admin_required
def admin_department_edit(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{dept.name}' updated.")
            return redirect('admin_department_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'hospital/admin/department_form.html', {'form': form, 'dept': dept, 'title': f"Edit {dept.name}"})


@admin_required
def admin_staff_list(request):
    staff_users = User.objects.filter(role__in=['admin', 'receptionist']).order_by('role', 'username')
    return render(request, 'hospital/admin/staff_list.html', {'staff_users': staff_users})


@admin_required
def admin_staff_create(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Staff member '{user.username}' created with role '{user.get_role_display()}'.")
            return redirect('admin_staff_list')
    else:
        form = StaffCreationForm()
    return render(request, 'hospital/admin/staff_form.html', {'form': form})


@admin_required
def admin_reports(request):
    # ORM aggregations per synopsis requirement
    doctor_workload = Doctor.objects.annotate(
        total_appts=Count('appointments'),
        completed_appts=Count('appointments', filter=Q(appointments__status='completed')),
        pending_appts=Count('appointments', filter=Q(appointments__status='pending')),
    ).select_related('user', 'department').order_by('-total_appts')

    top_diagnoses = MedicalRecord.objects.values('diagnosis').annotate(
        frequency=Count('id')
    ).order_by('-frequency')[:8]

    monthly_stats = []
    today = timezone.now().date()
    for i in range(5, -1, -1):
        target_month = today.replace(day=1) - timedelta(days=i*30)
        month_label = target_month.strftime('%b %Y')
        appts_count = Appointment.objects.filter(
            appointment_date__year=target_month.year,
            appointment_date__month=target_month.month
        ).count()
        rev = Invoice.objects.filter(
            issued_at__year=target_month.year,
            issued_at__month=target_month.month,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        monthly_stats.append({
            'month': month_label,
            'appointments': appts_count,
            'revenue': float(rev),
        })

    return render(request, 'hospital/admin/reports.html', {
        'doctor_workload': doctor_workload,
        'top_diagnoses': top_diagnoses,
        'monthly_stats': monthly_stats,
    })


# =====================================================================
# 3. DOCTOR VIEWS
# =====================================================================

@doctor_required
def doctor_dashboard(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    today = timezone.now().date()

    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).select_related('patient__user').order_by('appointment_time')

    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gt=today,
        status__in=['pending', 'confirmed']
    ).select_related('patient__user').order_by('appointment_date', 'appointment_time')[:10]

    stats = {
        'today_total': today_appointments.count(),
        'today_completed': today_appointments.filter(status='completed').count(),
        'today_pending': today_appointments.filter(status__in=['pending', 'confirmed']).count(),
        'all_time_completed': Appointment.objects.filter(doctor=doctor, status='completed').count(),
    }

    return render(request, 'hospital/doctor/dashboard.html', {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'stats': stats,
        'today': today,
    })


@doctor_required
def doctor_consultation(request, appointment_id):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)

    # Fetch or instantiate MedicalRecord
    record, created = MedicalRecord.objects.get_or_create(
        appointment=appointment,
        defaults={'patient': appointment.patient, 'diagnosis': ''}
    )

    # Fetch or instantiate PatientVital
    vitals, _ = PatientVital.objects.get_or_create(medical_record=record)

    if request.method == 'POST':
        record_form = MedicalRecordForm(request.POST, instance=record)
        vital_form = PatientVitalForm(request.POST, instance=vitals)
        formset = PrescriptionFormSet(request.POST, instance=record)

        if record_form.is_valid() and vital_form.is_valid() and formset.is_valid():
            record = record_form.save()
            vital_form.save()
            formset.save()

            # Mark appointment completed
            appointment.status = 'completed'
            appointment.save(update_fields=['status'])

            # Automatically create or update Invoice
            invoice, inv_created = Invoice.objects.get_or_create(
                appointment=appointment,
                defaults={'patient': appointment.patient, 'total_amount': 0.00, 'status': 'unpaid'}
            )
            # Rebuild invoice line items
            invoice.items.all().delete()
            # 1. Consultation fee
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Consultation Fee - Dr. {doctor.user.get_full_name()} ({doctor.specialization})",
                amount=doctor.consultation_fee
            )
            # 2. Prescribed medicines cost
            for pres in record.prescriptions.select_related('medicine').all():
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=f"Medicine: {pres.medicine.name} ({pres.dosage}) x {pres.duration_days} days",
                    amount=pres.medicine.unit_price
                )
            invoice.calculate_total()

            messages.success(request, f"Clinical consultation completed for {appointment.patient.user.get_full_name()}! Prescription and Invoice generated.")
            return redirect('printable_prescription', record_id=record.id)
        else:
            messages.error(request, "Please check form entries for errors.")
    else:
        record_form = MedicalRecordForm(instance=record)
        vital_form = PatientVitalForm(instance=vitals)
        formset = PrescriptionFormSet(instance=record)

    # Previous medical records for reference
    past_records = MedicalRecord.objects.filter(patient=appointment.patient)\
        .exclude(id=record.id).select_related('appointment__doctor__user').prefetch_related('prescriptions__medicine')[:5]

    return render(request, 'hospital/doctor/consultation.html', {
        'doctor': doctor,
        'appointment': appointment,
        'record': record,
        'record_form': record_form,
        'vital_form': vital_form,
        'formset': formset,
        'past_records': past_records,
    })


@doctor_required
def doctor_patient_history(request, patient_id):
    doctor = get_object_or_404(Doctor, user=request.user)
    patient = get_object_or_404(Patient, id=patient_id)
    records = MedicalRecord.objects.filter(patient=patient)\
        .select_related('appointment__doctor__user', 'vitals')\
        .prefetch_related('prescriptions__medicine').order_by('-created_at')

    return render(request, 'hospital/doctor/patient_history.html', {
        'patient': patient,
        'records': records,
        'doctor': doctor,
    })


# =====================================================================
# 4. RECEPTIONIST VIEWS
# =====================================================================

@receptionist_required
def receptionist_dashboard(request):
    today = timezone.now().date()

    today_appointments = Appointment.objects.filter(appointment_date=today)\
        .select_related('patient__user', 'doctor__user', 'doctor__department')\
        .order_by('appointment_time')

    unpaid_invoices = Invoice.objects.filter(status='unpaid')\
        .select_related('patient__user', 'appointment__doctor__user')\
        .order_by('-issued_at')[:8]

    stats = {
        'today_appointments_count': today_appointments.count(),
        'confirmed_count': today_appointments.filter(status='confirmed').count(),
        'pending_count': today_appointments.filter(status='pending').count(),
        'completed_count': today_appointments.filter(status='completed').count(),
        'unpaid_invoices_count': Invoice.objects.filter(status='unpaid').count(),
    }

    return render(request, 'hospital/receptionist/dashboard.html', {
        'today': today,
        'today_appointments': today_appointments,
        'unpaid_invoices': unpaid_invoices,
        'stats': stats,
    })


@staff_required
def receptionist_patient_list(request):
    search = request.GET.get('q', '').strip()
    patients = Patient.objects.select_related('user').all()
    if search:
        patients = patients.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(phone_number__icontains=search)
        )
    return render(request, 'hospital/receptionist/patient_list.html', {
        'patients': patients,
        'search': search,
    })


@staff_required
def receptionist_patient_create(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Patient {user.get_full_name()} registered with username '{user.username}'.")
            return redirect('receptionist_patient_list')
    else:
        form = PatientRegistrationForm()
    return render(request, 'hospital/receptionist/patient_form.html', {'form': form})


@staff_required
def receptionist_appointment_book(request):
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            try:
                appointment = form.save()
                messages.success(request, f"Appointment #{appointment.id} successfully booked for {appointment.patient.user.get_full_name()}!")
                return redirect('receptionist_dashboard')
            except Exception as e:
                form.add_error(None, str(e))
    else:
        initial_patient = request.GET.get('patient')
        form = AppointmentBookingForm(initial={'patient': initial_patient} if initial_patient else None)

    return render(request, 'hospital/receptionist/appointment_form.html', {'form': form})


@staff_required
def appointment_status_update(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    new_status = request.POST.get('status')
    if new_status in dict(Appointment.STATUS_CHOICES):
        appointment.status = new_status
        appointment.save(update_fields=['status'])
        messages.success(request, f"Appointment #{appointment.id} status changed to {appointment.get_status_display()}.")

    # Return to referer or dashboard
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer or 'dashboard_redirect')


@staff_required
def invoice_list(request):
    status_filter = request.GET.get('status', '')
    invoices = Invoice.objects.select_related('patient__user', 'appointment__doctor__user')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    return render(request, 'hospital/receptionist/invoice_list.html', {
        'invoices': invoices,
        'status_filter': status_filter,
    })


@staff_required
def invoice_collect_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        form = InvoicePaymentForm(request.POST, instance=invoice)
        if form.is_valid():
            inv = form.save(commit=False)
            if inv.status == 'paid' and not inv.paid_at:
                inv.paid_at = timezone.now()
            inv.save()
            messages.success(request, f"Invoice #{inv.id:05d} payment updated successfully.")
            return redirect('printable_invoice', invoice_id=inv.id)
    else:
        form = InvoicePaymentForm(instance=invoice)

    return render(request, 'hospital/receptionist/invoice_payment.html', {
        'invoice': invoice,
        'form': form,
    })


# =====================================================================
# 5. PATIENT VIEWS
# =====================================================================

@patient_required
def patient_dashboard(request):
    patient = get_object_or_404(Patient, user=request.user)
    today = timezone.now().date()

    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_date__gte=today
    ).exclude(status='cancelled').select_related('doctor__user', 'doctor__department').order_by('appointment_date')

    past_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_date__lt=today
    ).select_related('doctor__user', 'doctor__department').order_by('-appointment_date')[:5]

    medical_records = MedicalRecord.objects.filter(patient=patient)\
        .select_related('appointment__doctor__user')\
        .prefetch_related('prescriptions__medicine').order_by('-created_at')[:5]

    invoices = Invoice.objects.filter(patient=patient).order_by('-issued_at')[:5]

    return render(request, 'hospital/patient/dashboard.html', {
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'medical_records': medical_records,
        'invoices': invoices,
    })


@patient_required
def patient_appointment_book(request):
    patient = get_object_or_404(Patient, user=request.user)

    if request.method == 'POST':
        form = PatientSelfBookingForm(request.POST)
        if form.is_valid():
            try:
                appointment = form.save(commit=False)
                appointment.patient = patient
                appointment.status = 'pending'
                appointment.full_clean()  # Triggers models.py validation
                appointment.save()
                messages.success(request, f"Your appointment with {appointment.doctor} on {appointment.appointment_date} has been booked! Status: Pending Confirmation.")
                return redirect('patient_dashboard')
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = PatientSelfBookingForm()

    doctors = Doctor.objects.select_related('user', 'department').all()
    departments = Department.objects.all()

    return render(request, 'hospital/patient/book_appointment.html', {
        'form': form,
        'doctors': doctors,
        'departments': departments,
    })


@patient_required
def patient_appointment_cancel(request, appointment_id):
    patient = get_object_or_404(Patient, user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=patient)

    if appointment.status in ['pending', 'confirmed']:
        appointment.status = 'cancelled'
        appointment.save(update_fields=['status'])
        messages.info(request, f"Appointment #{appointment.id} has been cancelled.")
    else:
        messages.warning(request, "Completed or already cancelled appointments cannot be modified.")

    return redirect('patient_dashboard')


@patient_required
def patient_medical_records(request):
    patient = get_object_or_404(Patient, user=request.user)
    records = MedicalRecord.objects.filter(patient=patient)\
        .select_related('appointment__doctor__user', 'vitals')\
        .prefetch_related('prescriptions__medicine').order_by('-created_at')

    return render(request, 'hospital/patient/medical_records.html', {
        'patient': patient,
        'records': records,
    })


@login_required
def patient_record_detail(request, record_id):
    record = get_object_or_404(
        MedicalRecord.objects.select_related('patient__user', 'appointment__doctor__user', 'vitals'),
        id=record_id
    )
    user = request.user
    # Authorization check
    if not (user.is_superuser or user.role in ['admin', 'receptionist'] or
            (user.role == 'doctor' and record.appointment.doctor.user == user) or
            (user.role == 'patient' and record.patient.user == user)):
        return HttpResponseForbidden("You are not authorized to view this medical record.")

    return render(request, 'hospital/patient/record_detail.html', {'record': record})


# =====================================================================
# 6. PRINT / EXPORT VIEWS
# =====================================================================

@login_required
def printable_prescription(request, record_id):
    record = get_object_or_404(
        MedicalRecord.objects.select_related(
            'patient__user',
            'appointment__doctor__user',
            'appointment__doctor__department',
            'vitals'
        ).prefetch_related('prescriptions__medicine'),
        id=record_id
    )
    user = request.user
    # Authorization check
    if not (user.is_superuser or user.role in ['admin', 'receptionist'] or
            (user.role == 'doctor' and record.appointment.doctor.user == user) or
            (user.role == 'patient' and record.patient.user == user)):
        return HttpResponseForbidden("You are not authorized to view this prescription.")

    return render(request, 'hospital/print/prescription.html', {'record': record})


@login_required
def printable_invoice(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'patient__user',
            'appointment__doctor__user',
            'appointment__doctor__department'
        ).prefetch_related('items'),
        id=invoice_id
    )
    user = request.user
    # Authorization check
    if not (user.is_superuser or user.role in ['admin', 'receptionist'] or
            (user.role == 'patient' and invoice.patient.user == user)):
        return HttpResponseForbidden("You are not authorized to view this invoice.")

    return render(request, 'hospital/print/invoice.html', {'invoice': invoice})


# =====================================================================
# 7. AJAX / JSON API ENDPOINTS
# =====================================================================

def api_doctor_availability(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'doctor_id and date parameters required'}, status=400)

    try:
        doctor = Doctor.objects.get(id=doctor_id)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (Doctor.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid doctor or date format'}, status=400)

    is_available_day = doctor.is_available_on_date(target_date)
    booked_times = list(
        Appointment.objects.filter(
            doctor=doctor,
            appointment_date=target_date
        ).exclude(status='cancelled').values_list('appointment_time', flat=True)
    )
    booked_time_strings = [t.strftime('%H:%M') for t in booked_times]

    # Generate 30-min candidate slots
    slots = []
    current_time = datetime.combine(target_date, doctor.available_time_start)
    end_time = datetime.combine(target_date, doctor.available_time_end)

    while current_time < end_time:
        slot_str = current_time.strftime('%H:%M')
        slots.append({
            'time': slot_str,
            'is_booked': slot_str in booked_time_strings
        })
        current_time += timedelta(minutes=30)

    return JsonResponse({
        'doctor_name': doctor.user.get_full_name(),
        'available_days': doctor.get_available_days_list(),
        'is_available_day': is_available_day,
        'start_time': doctor.available_time_start.strftime('%H:%M'),
        'end_time': doctor.available_time_end.strftime('%H:%M'),
        'slots': slots,
    })


@admin_required
def api_analytics_data(request):
    # 1. Monthly appointments
    today = timezone.now().date()
    months = []
    appointment_counts = []
    revenue_totals = []

    for i in range(5, -1, -1):
        target_month = today.replace(day=1) - timedelta(days=i*30)
        months.append(target_month.strftime('%b %Y'))
        appts = Appointment.objects.filter(
            appointment_date__year=target_month.year,
            appointment_date__month=target_month.month
        ).count()
        appointment_counts.append(appts)

        rev = Invoice.objects.filter(
            issued_at__year=target_month.year,
            issued_at__month=target_month.month,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_totals.append(float(rev))

    # 2. Department distribution
    dept_labels = []
    dept_counts = []
    for dept in Department.objects.annotate(appts=Count('doctors__appointments')).all():
        dept_labels.append(dept.name)
        dept_counts.append(dept.appts)

    # 3. Top Diagnoses
    diagnoses_qs = MedicalRecord.objects.values('diagnosis').annotate(count=Count('id')).order_by('-count')[:5]
    diag_labels = [d['diagnosis'][:20] + ('...' if len(d['diagnosis']) > 20 else '') for d in diagnoses_qs]
    diag_counts = [d['count'] for d in diagnoses_qs]

    return JsonResponse({
        'monthly': {
            'labels': months,
            'appointments': appointment_counts,
            'revenue': revenue_totals,
        },
        'departments': {
            'labels': dept_labels,
            'data': dept_counts,
        },
        'diagnoses': {
            'labels': diag_labels,
            'data': diag_counts,
        }
    })
