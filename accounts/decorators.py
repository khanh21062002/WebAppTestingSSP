from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, 'Bạn không có quyền truy cập trang này.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.can_create_exam and not request.user.is_superuser:
            messages.error(request, 'Bạn không có quyền truy cập trang này.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
