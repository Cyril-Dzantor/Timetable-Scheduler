from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required,user_passes_test 
from django.contrib import messages
from .forms import CustomLoginForm, CustomRegisterForm,ComplaintForm 
from django.utils import timezone
from .models import Complaint 

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('redirect_by_role')
        else:
            messages.error(request, "Login failed. Check your details.")
            print(form.errors)

    else:
        form = CustomLoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def redirect_by_role(request):
    user = request.user
    if user.is_student and hasattr(user, 'student_profile'):
        return redirect('portal:student_dashboard')
    elif user.is_lecturer and hasattr(user, 'lecturer_profile'):
        return redirect('portal:lecturer_dashboard')
    elif user.is_admin and hasattr(user,'admin_profile'):
        return redirect('home')
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Check your details.")
    else:
        form = CustomRegisterForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def file_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            return redirect('complaint_list')
    else:
        form = ComplaintForm()
    return render(request, 'users/file_complaint.html', {'form': form})

@login_required
def complaint_list(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'users/complaint_list.html', {'complaints': complaints})

@user_passes_test(lambda u: u.is_admin)
def admin_complaints(request):
    complaints = Complaint.objects.all().order_by('-submitted_at')
    return render(request, 'users/admin_complaints.html', {'complaints': complaints})

@user_passes_test(lambda u: u.is_admin)
def respond_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        complaint.response = request.POST.get('response')
        complaint.status = request.POST.get('status')
        complaint.responded_at = timezone.now()
        complaint.save()
        return redirect('admin_complaints')
    return render(request, 'users/respond_complaint.html', {'complaint': complaint})