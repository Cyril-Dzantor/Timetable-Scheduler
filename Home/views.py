from django.shortcuts import render,redirect
from django.contrib.auth import logout

# Create your views here.
def home(request):
    return render(request, 'home/home.html')

def contact(request):
    return render(request,'home/contact.html')

def about(request):
    return render(request, 'home/about.html')

def logout_view(request):
    logout(request)
    return redirect('login')