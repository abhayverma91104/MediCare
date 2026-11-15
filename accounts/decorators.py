from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access that page.")
            return redirect('dashboard_redirect')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required(['admin'])(view_func)


def doctor_required(view_func):
    return role_required(['doctor'])(view_func)


def receptionist_required(view_func):
    return role_required(['receptionist'])(view_func)


def patient_required(view_func):
    return role_required(['patient'])(view_func)


def staff_required(view_func):
    return role_required(['admin', 'receptionist'])(view_func)


def clinical_staff_required(view_func):
    return role_required(['admin', 'doctor', 'receptionist'])(view_func)

