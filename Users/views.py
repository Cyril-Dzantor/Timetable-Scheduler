from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required,user_passes_test
from django.core.exceptions import PermissionDenied 
from django.contrib import messages
from .forms import CustomLoginForm, CustomRegisterForm,ComplaintForm 
from django.utils import timezone
from .models import Complaint 
from django.db.models import Q

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


@user_passes_test(lambda u: u.is_admin)
def respond_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Verify admin is from the same college as the complaint
    if request.user.admin_profile.college != complaint.college:
        raise PermissionDenied("You can only respond to complaints from your college")
    
    if request.method == 'POST':
        complaint.response = request.POST.get('response')
        complaint.status = request.POST.get('status')
        complaint.responded_at = timezone.now()
        complaint.save()
        return redirect('admin_complaints')
    return render(request, 'users/respond_complaint.html', {'complaint': complaint})

@login_required
def file_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            
            # Set college based on user type
            if hasattr(request.user, 'student_profile'):
                complaint.college = request.user.student_profile.college
            elif hasattr(request.user, 'lecturer_profile'):
                complaint.college = request.user.lecturer_profile.college
            
            complaint.save()
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        form = ComplaintForm()
    return render(request, 'users/file_complaint.html', {'form': form})

@login_required
def complaint_detail(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Verify college access
    if hasattr(request.user, 'admin_profile'):
        if request.user.admin_profile.college != complaint.college:
            raise PermissionDenied("You can only access complaints from your college")
    elif complaint.user != request.user:
        raise PermissionDenied("You can only view your own complaints")
    
    if request.user.is_staff or getattr(request.user, 'is_admin', False):
        base_template = 'home/base.html'
    else:
        base_template = 'portal/base.html'
    
    if request.method == 'POST':
        new_response = request.POST.get('response')
        if new_response:
            # Verify admin is from same college before allowing response
            if request.user.is_admin and request.user.admin_profile.college != complaint.college:
                raise PermissionDenied("You can only respond to complaints from your college")
            
            sender_name = "Admin" if request.user.is_admin else request.user.get_full_name() or request.user.email
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            formatted_response = f"{sender_name} ({timestamp}):\n{new_response}"
            
            if complaint.response:
                complaint.response = f"{complaint.response}\n\n---\n\n{formatted_response}"
            else:
                complaint.response = formatted_response
            
            if request.user.is_admin:
                complaint.status = request.POST.get('status', complaint.status)
            complaint.responded_at = timezone.now()
            complaint.save()
            return redirect('complaint_detail', complaint_id=complaint.id)
    
    return render(request, 'users/complaint_detail.html', {
        'complaint': complaint,
        'is_admin': request.user.is_admin,
        'base_template': base_template
    })
@login_required
def complaint_list(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'users/complaint_list.html', {'complaints': complaints})

@user_passes_test(lambda u: u.is_admin)
def admin_complaints(request):
    # Show complaints from the admin's college.
    # Include: (a) complaints with Complaint.college matching admin's college,
    # and (b) legacy complaints where college is null but the user's profile matches.
    admin_college = getattr(request.user.admin_profile, 'college', None)
    if not admin_college:
        complaints = Complaint.objects.none()
    else:
        complaints = Complaint.objects.filter(
            Q(college=admin_college)
            |
            Q(college__isnull=True, user__student_profile__college=admin_college)
            |
            Q(college__isnull=True, user__lecturer_profile__college=admin_college)
        ).order_by('-submitted_at')
    return render(request, 'users/admin_complaints.html', {'complaints': complaints})


@login_required
def profile_view(request):
    user = request.user
    base_template = 'home/base.html' if user.is_admin else 'portal/base.html'

    student_profile = getattr(user, 'student_profile', None)
    lecturer_profile = getattr(user, 'lecturer_profile', None)
    admin_profile = getattr(user, 'admin_profile', None)
    
    # Generate initials for the profile image
    initials = ''.join([name[0].upper() for name in user.get_full_name().split() if name]) or user.username[0].upper()
    
    context = {
        'base_template': base_template,
        'user_obj': user,
        'student_profile': student_profile,
        'lecturer_profile': lecturer_profile,
        'admin_profile': admin_profile,
        'initials': initials,  
    }
    return render(request, 'users/profile.html', context)