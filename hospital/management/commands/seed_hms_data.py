from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta
from hospital.models import (
    Department, Doctor, Patient, Appointment,
    MedicalRecord, PatientVital, Medicine, Prescription,
    Invoice, InvoiceItem
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial realistic data for MediCare Hospital Management System'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting MediCare HMS Database Seeder..."))

        # 1. Create Admin Account
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@medicare.hms',
                'first_name': 'Hospital',
                'last_name': 'Director',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("✓ Admin user created: admin / admin123"))

        # 2. Create Receptionist Account
        recep_user, _ = User.objects.get_or_create(
            username='receptionist',
            defaults={
                'email': 'reception@medicare.hms',
                'first_name': 'Sunita',
                'last_name': 'Mishra',
                'role': 'receptionist',
                'is_staff': False,
            }
        )
        recep_user.set_password('recep123')
        recep_user.save()
        self.stdout.write(self.style.SUCCESS("✓ Receptionist user created: receptionist / recep123"))

        # 3. Create Clinical Departments
        departments_data = [
            ("Cardiology", "Heart disease, arrhythmia, hypertension, and advanced cardiovascular diagnostics."),
            ("Neurology", "Brain, spinal cord, nervous system disorders, stroke care, and neuropathies."),
            ("Orthopedics", "Bone fractures, joint replacements, sports injuries, and musculoskeletal disorders."),
            ("Pediatrics", "Infant and child wellness, childhood immunizations, and pediatric care."),
            ("General Medicine", "Primary healthcare consultations, fever, acute infections, and lifestyle diseases."),
        ]
        dept_objs = {}
        for name, desc in departments_data:
            dept, _ = Department.objects.get_or_create(name=name, defaults={'description': desc})
            dept_objs[name] = dept
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(dept_objs)} clinical departments"))

        # 4. Create Specialist Doctors
        doctors_data = [
            {
                'username': 'dr_sharma',
                'email': 'dr.sharma@medicare.hms',
                'first_name': 'Rajesh',
                'last_name': 'Sharma',
                'department': dept_objs['Cardiology'],
                'specialization': 'Senior Interventional Cardiologist',
                'phone': '+91 9811002233',
                'fee': 800.00,
                'days': 'Mon,Tue,Wed,Thu,Fri,Sat',
                'start': time(9, 0),
                'end': time(17, 0),
            },
            {
                'username': 'dr_kapoor',
                'email': 'dr.kapoor@medicare.hms',
                'first_name': 'Ananya',
                'last_name': 'Kapoor',
                'department': dept_objs['Neurology'],
                'specialization': 'Consultant Neurologist',
                'phone': '+91 9822113344',
                'fee': 900.00,
                'days': 'Mon,Tue,Wed,Thu,Fri,Sat',
                'start': time(10, 0),
                'end': time(18, 0),
            },
            {
                'username': 'dr_gupta',
                'email': 'dr.gupta@medicare.hms',
                'first_name': 'Vikram',
                'last_name': 'Gupta',
                'department': dept_objs['Orthopedics'],
                'specialization': 'Orthopedic & Joint Surgeon',
                'phone': '+91 9833224455',
                'fee': 600.00,
                'days': 'Mon,Tue,Wed,Thu,Fri,Sat',
                'start': time(9, 0),
                'end': time(16, 0),
            },
            {
                'username': 'dr_mehta',
                'email': 'dr.mehta@medicare.hms',
                'first_name': 'Pooja',
                'last_name': 'Mehta',
                'department': dept_objs['Pediatrics'],
                'specialization': 'Child Specialist & Neonatologist',
                'phone': '+91 9844335566',
                'fee': 500.00,
                'days': 'Mon,Tue,Wed,Thu,Fri,Sat',
                'start': time(9, 30),
                'end': time(16, 30),
            },
            {
                'username': 'dr_verma',
                'email': 'dr.verma@medicare.hms',
                'first_name': 'Alok',
                'last_name': 'Verma',
                'department': dept_objs['General Medicine'],
                'specialization': 'Consultant Physician',
                'phone': '+91 9855446677',
                'fee': 450.00,
                'days': 'Mon,Tue,Wed,Thu,Fri,Sat',
                'start': time(8, 30),
                'end': time(17, 30),
            },
        ]
        doc_objs = []
        for d in doctors_data:
            user, _ = User.objects.get_or_create(
                username=d['username'],
                defaults={
                    'email': d['email'],
                    'first_name': d['first_name'],
                    'last_name': d['last_name'],
                    'role': 'doctor',
                }
            )
            user.set_password('doctor123')
            user.save()

            doctor, _ = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'department': d['department'],
                    'specialization': d['specialization'],
                    'phone_number': d['phone'],
                    'consultation_fee': d['fee'],
                    'available_days': d['days'],
                    'available_time_start': d['start'],
                    'available_time_end': d['end'],
                }
            )
            doc_objs.append(doctor)
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(doc_objs)} doctors with credentials (password: doctor123)"))

        # 5. Create Essential Medicines
        medicines_data = [
            ("Paracetamol 650mg", "tablet", 30.00, 500),
            ("Amoxicillin 500mg", "capsule", 85.00, 300),
            ("Atorvastatin 10mg", "tablet", 120.00, 250),
            ("Metformin 500mg", "tablet", 45.00, 400),
            ("Ibuprofen 400mg", "tablet", 40.00, 350),
            ("Azithromycin 500mg", "tablet", 110.00, 200),
            ("Omeprazole 20mg", "capsule", 60.00, 300),
            ("Cetirizine 10mg", "tablet", 25.00, 450),
            ("Cough Syrup (Dex)", "syrup", 95.00, 150),
            ("Diclofenac Gel", "ointment", 75.00, 180),
            ("Normal Saline 100ml", "injection", 50.00, 200),
            ("Pantoprazole 40mg", "tablet", 70.00, 320),
        ]
        med_objs = {}
        for name, form, price, qty in medicines_data:
            med, _ = Medicine.objects.get_or_create(
                name=name,
                defaults={'dosage_form': form, 'unit_price': price, 'stock_quantity': qty}
            )
            med_objs[name] = med
        self.stdout.write(self.style.SUCCESS(f"✓ Stocked {len(med_objs)} pharmacy medicines"))

        # 6. Create Patients
        patients_data = [
            {
                'username': 'rahul_verma',
                'email': 'rahul.verma@example.com',
                'first_name': 'Rahul',
                'last_name': 'Verma',
                'dob': date(1996, 4, 15),
                'gender': 'M',
                'blood': 'A+',
                'phone': '+91 9811223344',
                'address': 'B-42, Sector 62, Noida, UP',
                'emergency': '+91 9811223300',
            },
            {
                'username': 'priya_singh',
                'email': 'priya.singh@example.com',
                'first_name': 'Priya',
                'last_name': 'Singh',
                'dob': date(1990, 8, 22),
                'gender': 'F',
                'blood': 'B+',
                'phone': '+91 9877665544',
                'address': 'Flat 304, Green Heights, Indirapuram, Ghaziabad',
                'emergency': '+91 9877665500',
            },
            {
                'username': 'amit_patel',
                'email': 'amit.patel@example.com',
                'first_name': 'Amit',
                'last_name': 'Patel',
                'dob': date(1979, 12, 5),
                'gender': 'M',
                'blood': 'O+',
                'phone': '+91 9711445566',
                'address': 'Plot 12, Sector 15, Vasundhara, Ghaziabad',
                'emergency': '+91 9711445500',
            },
            {
                'username': 'sneha_sharma',
                'email': 'sneha.sharma@example.com',
                'first_name': 'Sneha',
                'last_name': 'Sharma',
                'dob': date(2002, 1, 18),
                'gender': 'F',
                'blood': 'AB+',
                'phone': '+91 9988776655',
                'address': 'Hostel 4, JIIT Campus, Noida',
                'emergency': '+91 9988776600',
            },
        ]
        patient_objs = []
        for p in patients_data:
            user, _ = User.objects.get_or_create(
                username=p['username'],
                defaults={
                    'email': p['email'],
                    'first_name': p['first_name'],
                    'last_name': p['last_name'],
                    'role': 'patient',
                }
            )
            user.set_password('patient123')
            user.save()

            patient, _ = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'date_of_birth': p['dob'],
                    'gender': p['gender'],
                    'blood_group': p['blood'],
                    'phone_number': p['phone'],
                    'address': p['address'],
                    'emergency_contact': p['emergency'],
                }
            )
            patient_objs.append(patient)
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(patient_objs)} patients (password: patient123)"))

        # 7. Create Sample Appointments, Clinical Records, Vitals, Prescriptions, and Invoices
        today = timezone.now().date()
        doc_sharma = doc_objs[0]  # Cardio
        doc_kapoor = doc_objs[1]  # Neuro
        doc_verma = doc_objs[4]   # General

        # Appt 1: Completed today with Dr. Sharma (Rahul Verma)
        appt1, _ = Appointment.objects.get_or_create(
            patient=patient_objs[0],
            doctor=doc_sharma,
            appointment_date=today,
            appointment_time=time(10, 0),
            defaults={
                'status': 'completed',
                'reason': 'Experiencing mild chest tightness and shortness of breath during morning walks.'
            }
        )
        rec1, _ = MedicalRecord.objects.get_or_create(
            appointment=appt1,
            defaults={
                'patient': patient_objs[0],
                'symptoms': 'Mild exertional dyspnea, normal S1/S2 heart sounds, no peripheral edema.',
                'diagnosis': 'Stage 1 Essential Hypertension with mild dyspnea',
                'notes': 'Reduce dietary sodium intake, light walking 30 mins daily, avoid strenuous physical strain.'
            }
        )
        PatientVital.objects.get_or_create(
            medical_record=rec1,
            defaults={
                'blood_pressure': '138/88 mmHg',
                'pulse_rate': 78,
                'temperature': 98.4,
                'weight': 74.5,
                'oxygen_saturation': 98
            }
        )
        Prescription.objects.get_or_create(
            medical_record=rec1,
            medicine=med_objs['Atorvastatin 10mg'],
            defaults={'dosage': '10mg', 'frequency': '1 tablet at bedtime', 'duration_days': 30, 'instructions': 'Take after dinner'}
        )
        Prescription.objects.get_or_create(
            medical_record=rec1,
            medicine=med_objs['Paracetamol 650mg'],
            defaults={'dosage': '650mg', 'frequency': 'SOS (as needed)', 'duration_days': 5, 'instructions': 'Take after food if headache occurs'}
        )
        inv1, _ = Invoice.objects.get_or_create(
            appointment=appt1,
            defaults={
                'patient': patient_objs[0],
                'status': 'paid',
                'payment_method': 'card',
                'paid_at': timezone.now()
            }
        )
        inv1.items.all().delete()
        InvoiceItem.objects.create(invoice=inv1, description="Cardiology Consultation Fee - Dr. Rajesh Sharma", amount=doc_sharma.consultation_fee)
        InvoiceItem.objects.create(invoice=inv1, description="Medicine: Atorvastatin 10mg x 30 days", amount=120.00)
        InvoiceItem.objects.create(invoice=inv1, description="Medicine: Paracetamol 650mg", amount=30.00)
        inv1.calculate_total()

        # Appt 2: Completed visit with Dr. Verma (Priya Singh)
        appt2, _ = Appointment.objects.get_or_create(
            patient=patient_objs[1],
            doctor=doc_verma,
            appointment_date=today - timedelta(days=2),
            appointment_time=time(11, 30),
            defaults={
                'status': 'completed',
                'reason': 'High fever, sore throat, and severe dry cough since 3 days.'
            }
        )
        rec2, _ = MedicalRecord.objects.get_or_create(
            appointment=appt2,
            defaults={
                'patient': patient_objs[1],
                'symptoms': 'Pharyngeal erythema present, temp 101.8°F, clear chest auscultation.',
                'diagnosis': 'Acute Bacterial Pharyngitis & Upper Respiratory Infection',
                'notes': 'Warm saline gargles 3-4 times daily, plenty of warm fluids, steam inhalation.'
            }
        )
        PatientVital.objects.get_or_create(
            medical_record=rec2,
            defaults={
                'blood_pressure': '118/76 mmHg',
                'pulse_rate': 86,
                'temperature': 101.8,
                'weight': 58.0,
                'oxygen_saturation': 97
            }
        )
        Prescription.objects.get_or_create(
            medical_record=rec2,
            medicine=med_objs['Amoxicillin 500mg'],
            defaults={'dosage': '500mg', 'frequency': '1-0-1 after meals', 'duration_days': 5, 'instructions': 'Complete the full antibiotic course'}
        )
        Prescription.objects.get_or_create(
            medical_record=rec2,
            medicine=med_objs['Cough Syrup (Dex)'],
            defaults={'dosage': '10ml', 'frequency': 'Three times daily', 'duration_days': 5, 'instructions': 'Take with warm water'}
        )
        inv2, _ = Invoice.objects.get_or_create(
            appointment=appt2,
            defaults={
                'patient': patient_objs[1],
                'status': 'paid',
                'payment_method': 'upi',
                'paid_at': timezone.now() - timedelta(days=2)
            }
        )
        inv2.items.all().delete()
        InvoiceItem.objects.create(invoice=inv2, description="General Consultation Fee - Dr. Alok Verma", amount=doc_verma.consultation_fee)
        InvoiceItem.objects.create(invoice=inv2, description="Medicine: Amoxicillin 500mg x 5 days", amount=85.00)
        InvoiceItem.objects.create(invoice=inv2, description="Medicine: Cough Syrup (Dex)", amount=95.00)
        inv2.calculate_total()

        # Appt 3: Confirmed in queue today (Amit Patel with Dr. Sharma)
        Appointment.objects.get_or_create(
            patient=patient_objs[2],
            doctor=doc_sharma,
            appointment_date=today,
            appointment_time=time(11, 0),
            defaults={
                'status': 'confirmed',
                'reason': 'Routine 6-month cardiovascular follow-up and ECG review.'
            }
        )

        # Appt 4: Pending arrival today (Sneha Sharma with Dr. Kapoor)
        Appointment.objects.get_or_create(
            patient=patient_objs[3],
            doctor=doc_kapoor,
            appointment_date=today,
            appointment_time=time(14, 0),
            defaults={
                'status': 'pending',
                'reason': 'Persistent unilateral migraine headaches with visual aura during study hours.'
            }
        )

        # Appt 5: Future upcoming appointment (Amit Patel with Dr. Verma)
        Appointment.objects.get_or_create(
            patient=patient_objs[2],
            doctor=doc_verma,
            appointment_date=today + timedelta(days=3),
            appointment_time=time(10, 30),
            defaults={
                'status': 'pending',
                'reason': 'Routine blood glucose monitoring and general checkup.'
            }
        )

        self.stdout.write(self.style.SUCCESS("✓ Seeded realistic clinical appointments, records, vitals, prescriptions & invoices"))
        self.stdout.write(self.style.SUCCESS("\n=============================================================="))
        self.stdout.write(self.style.SUCCESS(" MediCare HMS Demo Environment Ready!"))
        self.stdout.write(self.style.SUCCESS(" Admin:        username: admin         password: admin123"))
        self.stdout.write(self.style.SUCCESS(" Doctor:       username: dr_sharma     password: doctor123"))
        self.stdout.write(self.style.SUCCESS(" Receptionist: username: receptionist  password: recep123"))
        self.stdout.write(self.style.SUCCESS(" Patient:      username: rahul_verma   password: patient123"))
        self.stdout.write(self.style.SUCCESS("=============================================================="))

