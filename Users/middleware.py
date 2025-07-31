from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class RoleBasedAccessMiddleware:
    """
    Middleware to restrict access to admin-only URLs for students and lecturers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Admin-only URL patterns that students/lecturers shouldn't access
        self.admin_only_patterns = [
            '/timetable/',
            '/scheduler/',
            '/generate_schedule',
            '/generate_exam_schedule',
            '/rooms/',
            '/classes/',
            '/lecturers/',
            '/courses/',
            '/admin/',
        ]
        
        # Portal URLs that are safe for all users
        self.portal_patterns = [
            '/portal/',
            '/home/home',
            '/home/about',
            '/home/contact',
            '/login',
            '/logout',
            '/register',
            '/complaint',
        ]
    
    def __call__(self, request):
        # Check if user is authenticated and not an admin
        if request.user.is_authenticated and not request.user.is_admin:
            current_path = request.path
            
            # Check if current path is admin-only
            is_admin_only = any(pattern in current_path for pattern in self.admin_only_patterns)
            
            # Check if current path is in portal (safe)
            is_portal = any(pattern in current_path for pattern in self.portal_patterns)
            
            # If trying to access admin-only URL, redirect to appropriate portal
            if is_admin_only and not is_portal:
                messages.warning(request, "Access denied. This area is for administrators only.")
                
                if request.user.is_student:
                    return redirect('portal:student_dashboard')
                elif request.user.is_lecturer:
                    return redirect('portal:lecturer_dashboard')
                else:
                    return redirect('/home/home')
        
        response = self.get_response(request)
        return response 