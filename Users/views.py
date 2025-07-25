from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm, CustomRegisterForm

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