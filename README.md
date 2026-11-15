# MediCare - Hospital Management System (HMS)

> **Academic Project Submission**: Jaypee Institute of Information Technology (JIIT)  
> **Course**: Full-Stack Web Development  
> **Supervisor**: Dr. Diksha Pandey  
> **Project Team**:
> - Guneet Chhabra (2401200036)
> - Abhay Verma (2401200051)
> - Utkarsh Singh (2401200055)
> - Krishnam Dalmia (2401200060)

---

## 🏥 Overview

The **MediCare Hospital Management System (HMS)** is a full-stack web application built using Python and the Django framework. Designed to replace paper-based clinic workflows, the system provides a secure, role-based platform connecting **Hospital Administrators**, **Specialist Doctors**, **Front-Desk Receptionists**, and **Patients**.

The application goes beyond basic CRUD operations by incorporating real-world clinical features such as **real-time appointment conflict prevention**, **patient vitals and triage**, **dynamic formset-driven prescription authoring**, **automated billing and invoicing**, and **Chart.js visual analytics**.

---

## 🚀 Key Features

### 1. 🛡️ Role-Based Authentication & Authorization
- Custom `User` model extending `AbstractUser` with 4 distinct roles: `admin`, `doctor`, `receptionist`, and `patient`.
- Role-specific access control decorators (`@admin_required`, `@doctor_required`, `@receptionist_required`, `@patient_required`).
- Intelligent login routing redirecting users automatically to their respective role dashboards.

### 2. 📅 Intelligent Appointment Scheduling & Conflict Prevention
- Real-time double-booking validation on `(doctor, appointment_date, appointment_time)`.
- Enforces doctor working days (e.g., Mon–Sat) and clinic shift hours (e.g., 09:00 – 17:00).
- Rejects past date selections and time slot collisions.
- Dynamic slot availability helper widget via `/api/doctor-availability/` JSON endpoint.

### 3. 🩺 Clinical Consultation & Dynamic Digital Prescriptions (Rx)
- Doctor workspace with patient health overview and chief complaints.
- **Patient Vitals Recording**: Blood Pressure (mmHg), Pulse (bpm), Body Temp (°F), Weight (kg), and $\text{SpO}_2$ (%).
- **Dynamic Prescription Formset**: Add and remove multiple medications dynamically on the same page.
- **Official Printable Prescription (Rx)**: Standard medical letterhead format ready for printing or saving as PDF with doctor signature line and clinic stamp.

### 4. 💳 Integrated Billing & Invoicing Engine
- Automatic generation of invoices upon consultation completion.
- Dynamic itemization: Doctor consultation fee + prescribed pharmacy medications.
- Front-desk payment collection supporting **Cash**, **Card**, **UPI**, and **Insurance**.
- Printable official tax receipts with payment verification stamps.

### 5. 📊 Administrative Analytics & Django ORM Aggregations
- Quantitative reports on doctor workload using `Count('appointments')` and completion rates.
- Diagnostic condition frequency ranking using `annotate()` and `Count()`.
- Interactive **Chart.js** charts for 6-month visit trends and departmental patient distribution.

### 6. ⚡ Built-in Demo Data Seeder (`seed_hms_data`)
- Pre-loads clinical departments, 5 specialist doctors, 12 essential medicines, sample patients, active appointments, vitals, prescriptions, and billing receipts for immediate demonstration and viva presentation.

---

## 👥 Demo User Accounts & Credentials

Run `python manage.py seed_hms_data` to automatically create all demo accounts:

| Role | Username | Password | Notes |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full administrative oversight, staff management, and system reports |
| **Doctor** | `dr_sharma` | `doctor123` | Senior Cardiologist (Mon–Sat, 09:00–17:00, Fee ₹800) |
| **Doctor** | `dr_kapoor` | `doctor123` | Consultant Neurologist (Mon–Sat, 10:00–18:00, Fee ₹900) |
| **Doctor** | `dr_verma` | `doctor123` | Consultant Physician (General Medicine) |
| **Receptionist** | `receptionist` | `recep123` | Front-desk triage, walk-ins, scheduling, and billing desk |
| **Patient** | `rahul_verma` | `patient123` | Registered patient with prior clinical history |
| **Patient** | `priya_singh` | `patient123` | Registered patient with prior prescriptions |

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14+, Django 6.1
- **Database**: SQLite (built-in, zero external dependencies for evaluation) / PostgreSQL compatible
- **Frontend**: Django Templates, Bootstrap 5.3, Bootstrap Icons, Google Fonts (Plus Jakarta Sans)
- **Data Visualization**: Chart.js
- **Form Handling**: Django `ModelForm`, `inlineformset_factory`
- **Testing**: Django Test Suite (`unittest`)

---

## 💻 Getting Started & Running Locally

### 1. Prerequisites
Ensure Python 3.10+ is installed on your machine.

### 2. Activate Virtual Environment
```bash
# On macOS / Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py migrate
```

### 5. Seed Demonstration Data
Populate realistic departments, doctors, patients, appointments, and records:
```bash
python manage.py seed_hms_data
```

### 6. Launch the Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🧪 Running Automated Tests

A comprehensive test suite verifies user roles, double-booking logic, clinical formsets, invoice calculations, and role-based access security:

```bash
python manage.py test
```

Expected output:
```text
Ran 7 tests in 3.733s

OK
```

---

## 📂 Project Directory Structure

```text
├── Hospital_Management_System_Synopsis.pdf   # Original JIIT Project Synopsis
├── manage.py                                 # Django CLI executable
├── requirements.txt                          # Python dependencies
├── db.sqlite3                                # Development database with seed data
├── hospital_system/                          # Project root configuration
│   ├── settings.py                           # App settings, DB config, Auth redirects
│   ├── urls.py                               # Global URL routing
│   └── wsgi.py
├── accounts/                                 # User & Authentication App
│   ├── models.py                             # Custom User model (role choices)
│   ├── forms.py                              # Login & Patient registration forms
│   ├── views.py                              # Login, Logout, Profile, Role redirector
│   ├── decorators.py                         # Role-based authorization wrappers
│   └── urls.py
├── hospital/                                 # HMS Core Domain App
│   ├── models.py                             # Department, Doctor, Patient, Appointment,
│   │                                         # MedicalRecord, PatientVital, Medicine,
│   │                                         # Prescription, Invoice, InvoiceItem
│   ├── forms.py                              # ModelForms, Vitals form, PrescriptionFormSet
│   ├── views.py                              # Dashboards, Scheduling, Clinical, Billing
│   ├── admin.py                              # Customized Django Admin panel
│   ├── urls.py                               # All role portals and API endpoints
│   ├── tests.py                              # Automated validation test cases
│   └── management/commands/
│       └── seed_hms_data.py                  # Management command for demo data
└── templates/                                # Presentation Layer (Bootstrap 5)
    ├── base.html                             # Master layout, navigation, and alerts
    ├── accounts/                             # Sign-in, Patient registration, Profile
    └── hospital/
        ├── home.html                         # Public landing page
        ├── doctor_directory.html             # Public specialist directory & schedules
        ├── admin/                            # Dashboard, Doctor/Dept/Staff CRUD, Reports
        ├── doctor/                           # Daily queue, Clinical consultation, History
        ├── receptionist/                     # Triage desk, Patient registry, Billing
        ├── patient/                          # Patient portal, Self-booking, Records
        └── print/                            # Printable Rx Letterhead & Tax Invoice
```
