from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserLoginForm, PatientRegistrationForm
from hospital.models import Doctor, Patient


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


def register_patient_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to the Hospital Management System.")
            return redirect('patient_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_redirect_view(request):
    user = request.user
    if user.is_superuser or user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'doctor':
        return redirect('doctor_dashboard')
    elif user.role == 'receptionist':
        return redirect('receptionist_dashboard')
    elif user.role == 'patient':
        return redirect('patient_dashboard')
    return redirect('home')


@login_required
def profile_view(request):
    user = request.user
    doctor_profile = getattr(user, 'doctor_profile', None)
    patient_profile = getattr(user, 'patient_profile', None)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        if first_name and email:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            if doctor_profile:
                doctor_profile.phone_number = request.POST.get('phone_number', doctor_profile.phone_number)
                doctor_profile.specialization = request.POST.get('specialization', doctor_profile.specialization)
                doctor_profile.save()

            if patient_profile:
                patient_profile.phone_number = request.POST.get('phone_number', patient_profile.phone_number)
                patient_profile.address = request.POST.get('address', patient_profile.address)
                patient_profile.emergency_contact = request.POST.get('emergency_contact', patient_profile.emergency_contact)
                patient_profile.save()

            messages.success(request, "Your profile has been updated.")
            return redirect('profile')
        else:
            messages.error(request, "First name and email are required.")

    return render(request, 'accounts/profile.html', {
        'user': user,
        'doctor_profile': doctor_profile,
        'patient_profile': patient_profile,
    })
