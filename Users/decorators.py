from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Decorator to restrict access to admin users only.
    Redirects students and lecturers to the portal.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_admin:
            messages.warning(request, "Access denied. This area is for administrators only.")
            if request.user.is_student:
                return redirect('portal:student_dashboard')
            elif request.user.is_lecturer:
                return redirect('portal:lecturer_dashboard')
            else:
                return redirect('/home/home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def student_required(view_func):
    """
    Decorator to restrict access to students only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_student:
            messages.warning(request, "Access denied. This area is for students only.")
            return redirect('/home/home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def lecturer_required(view_func):
    """
    Decorator to restrict access to lecturers only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_lecturer:
            messages.warning(request, "Access denied. This area is for lecturers only.")
            return redirect('/home/home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view 