# portal/urls.py
from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('lecturer-dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('profile/', views.portal_profile, name='portal_profile'), 
    path('portal_home',views.portal_home, name='portal_home'),
]
