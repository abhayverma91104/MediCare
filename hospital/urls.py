from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('doctors/', views.doctor_directory, name='doctor_directory'),

    # Admin Portal
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/doctors/', views.admin_doctor_list, name='admin_doctor_list'),
    path('admin-portal/doctors/add/', views.admin_doctor_create, name='admin_doctor_create'),
    path('admin-portal/doctors/<int:doctor_id>/edit/', views.admin_doctor_edit, name='admin_doctor_edit'),
    path('admin-portal/doctors/<int:doctor_id>/delete/', views.admin_doctor_delete, name='admin_doctor_delete'),
    path('admin-portal/departments/', views.admin_department_list, name='admin_department_list'),
    path('admin-portal/departments/add/', views.admin_department_create, name='admin_department_create'),
    path('admin-portal/departments/<int:dept_id>/edit/', views.admin_department_edit, name='admin_department_edit'),
    path('admin-portal/staff/', views.admin_staff_list, name='admin_staff_list'),
    path('admin-portal/staff/add/', views.admin_staff_create, name='admin_staff_create'),
    path('admin-portal/reports/', views.admin_reports, name='admin_reports'),

    # Doctor Portal
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/consultation/<int:appointment_id>/', views.doctor_consultation, name='doctor_consultation'),
    path('doctor/patient/<int:patient_id>/history/', views.doctor_patient_history, name='doctor_patient_history'),

    # Receptionist Portal
    path('receptionist-dashboard/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('receptionist/patients/', views.receptionist_patient_list, name='receptionist_patient_list'),
    path('receptionist/patients/add/', views.receptionist_patient_create, name='receptionist_patient_create'),
    path('receptionist/appointments/book/', views.receptionist_appointment_book, name='receptionist_appointment_book'),
    path('receptionist/appointments/<int:appointment_id>/status/', views.appointment_status_update, name='appointment_status_update'),
    path('receptionist/invoices/', views.invoice_list, name='invoice_list'),
    path('receptionist/invoices/<int:invoice_id>/pay/', views.invoice_collect_payment, name='invoice_collect_payment'),

    # Patient Portal
    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/book-appointment/', views.patient_appointment_book, name='patient_appointment_book'),
    path('patient/appointments/<int:appointment_id>/cancel/', views.patient_appointment_cancel, name='patient_appointment_cancel'),
    path('patient/medical-records/', views.patient_medical_records, name='patient_medical_records'),
    path('patient/medical-records/<int:record_id>/', views.patient_record_detail, name='patient_record_detail'),

    # Print / Export
    path('print/prescription/<int:record_id>/', views.printable_prescription, name='printable_prescription'),
    path('print/invoice/<int:invoice_id>/', views.printable_invoice, name='printable_invoice'),

    # AJAX API Endpoints
    path('api/doctor-availability/', views.api_doctor_availability, name='api_doctor_availability'),
    path('api/analytics-data/', views.api_analytics_data, name='api_analytics_data'),
]

