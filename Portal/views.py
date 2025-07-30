from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from Users.models import User

def student_dashboard(request):
    return render(request, "portal/student_dashboard.html")

def lecturer_dashboard(request):
    return render(request, "portal/lecturer_dashboard.html")

@login_required
def portal_profile(request):
    return HttpResponse("This is your profile page.")

@login_required
def portal_home(request):
    user = request.user
    if user.is_student and hasattr(user, 'student_profile'):
        return redirect('portal:student_dashboard')
    elif user.is_lecturer and hasattr(user, 'lecturer_profile'):
        return redirect('portal:lecturer_dashboard')
