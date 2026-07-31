# decorator so I don't have to repeat role-checking logic in every view

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Use like:
        @role_required('hospital_staff')
        def update_availability(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(request, "You don't have permission to access that page.")
                return redirect('dashboard:home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator