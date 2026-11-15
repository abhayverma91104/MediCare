from datetime import date, time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from hospital.models import (
    Department, Doctor, Patient, Appointment,
    MedicalRecord, PatientVital, Medicine, Prescription,
    Invoice, InvoiceItem
)

User = get_user_model()


class HospitalManagementSystemTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Create Users
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )
        self.doc_user = User.objects.create_user(
            username='test_doctor',
            email='doctor@test.com',
            password='password123',
            first_name='Aditi',
            last_name='Rao',
            role='doctor'
        )
        self.recep_user = User.objects.create_user(
            username='test_recep',
            email='recep@test.com',
            password='password123',
            role='receptionist'
        )
        self.patient_user = User.objects.create_user(
            username='test_patient',
            email='patient@test.com',
            password='password123',
            first_name='Rohan',
            last_name='Mehra',
            role='patient'
        )

        # 2. Department & Doctor Profile
        self.dept = Department.objects.create(name='Cardiology', description='Heart care')
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            department=self.dept,
            specialization='Cardiologist',
            phone_number='9876543210',
            consultation_fee=600.00,
            available_days='Mon,Tue,Wed,Thu,Fri,Sat',
            available_time_start=time(9, 0),
            available_time_end=time(17, 0)
        )

        # 3. Patient Profile
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth=date(1995, 5, 10),
            gender='M',
            blood_group='O+',
            phone_number='9123456780',
            address='Noida Sector 62'
        )

        # 4. Medicine
        self.medicine = Medicine.objects.create(
            name='Aspirin 75mg',
            dosage_form='tablet',
            unit_price=25.00,
            stock_quantity=100
        )

    def test_user_roles(self):
        self.assertTrue(self.admin_user.is_admin_user)
        self.assertTrue(self.doc_user.is_doctor_user)
        self.assertTrue(self.recep_user.is_receptionist_user)
        self.assertTrue(self.patient_user.is_patient_user)

    def test_doctor_availability_logic(self):
        # Doctor is available Mon-Sat
        mon = date(2026, 11, 16)  # Monday
        sun = date(2026, 11, 22)  # Sunday
        self.assertTrue(self.doctor.is_available_on_date(mon))
        self.assertFalse(self.doctor.is_available_on_date(sun))

    def test_appointment_double_booking_prevention(self):
        # Target weekday
        target_date = date.today() + timedelta(days=2)
        while not self.doctor.is_available_on_date(target_date):
            target_date += timedelta(days=1)

        appt1 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=target_date,
            appointment_time=time(10, 0),
            reason='Heart palpitations'
        )
        self.assertIsNotNone(appt1.pk)

        # Attempt duplicate booking for same doctor at same date & time
        appt2 = Appointment(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=target_date,
            appointment_time=time(10, 0),
            reason='Second consultation'
        )
        with self.assertRaises(ValidationError):
            appt2.clean()

    def test_appointment_outside_working_hours(self):
        target_date = date.today() + timedelta(days=1)
        while not self.doctor.is_available_on_date(target_date):
            target_date += timedelta(days=1)

        # 08:00 is before doctor's 09:00 start
        early_appt = Appointment(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=target_date,
            appointment_time=time(8, 0),
            reason='Early visit'
        )
        with self.assertRaises(ValidationError):
            early_appt.clean()

    def test_clinical_consultation_flow(self):
        target_date = date.today()
        while not self.doctor.is_available_on_date(target_date):
            target_date += timedelta(days=1)

        appt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=target_date,
            appointment_time=time(14, 0),
            reason='Hypertension check'
        )

        # Doctor logs in and performs consultation
        self.client.login(username='test_doctor', password='password123')
        post_data = {
            'symptoms': 'Chest tightness and high stress',
            'diagnosis': 'Stage 1 Hypertension',
            'notes': 'Daily exercise and low salt',
            'blood_pressure': '135/85 mmHg',
            'pulse_rate': 76,
            'temperature': '98.6',
            'weight': '72.0',
            'oxygen_saturation': 99,
            # Formset management fields
            'prescriptions-TOTAL_FORMS': '1',
            'prescriptions-INITIAL_FORMS': '0',
            'prescriptions-MIN_NUM_FORMS': '0',
            'prescriptions-MAX_NUM_FORMS': '1000',
            # Form 0
            'prescriptions-0-medicine': self.medicine.id,
            'prescriptions-0-dosage': '75mg',
            'prescriptions-0-frequency': 'Once daily after breakfast',
            'prescriptions-0-duration_days': '14',
            'prescriptions-0-instructions': 'Take with water',
        }
        response = self.client.post(reverse('doctor_consultation', args=[appt.id]), post_data)
        self.assertEqual(response.status_code, 302)

        # Verify appointment marked completed
        appt.refresh_from_db()
        self.assertEqual(appt.status, 'completed')

        # Verify MedicalRecord & Vitals created
        record = appt.medical_record
        self.assertEqual(record.diagnosis, 'Stage 1 Hypertension')
        self.assertEqual(record.vitals.blood_pressure, '135/85 mmHg')

        # Verify prescription created
        self.assertEqual(record.prescriptions.count(), 1)
        self.assertEqual(record.prescriptions.first().medicine, self.medicine)

        # Verify invoice automatically generated
        self.assertTrue(hasattr(appt, 'invoice'))
        invoice = appt.invoice
        # Consultation fee (600) + medicine unit price (25) = 625.00
        self.assertEqual(invoice.total_amount, 625.00)

    def test_role_based_access_controls(self):
        # Patient cannot access admin dashboard
        self.client.login(username='test_patient', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected away

        # Admin can access admin dashboard
        self.client.login(username='test_admin', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_json_api_endpoints(self):
        target_date = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('api_doctor_availability'), {
            'doctor_id': self.doctor.id,
            'date': target_date
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('slots', data)
        self.assertIn('available_days', data)
