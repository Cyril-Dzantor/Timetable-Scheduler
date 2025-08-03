from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('generate_schedule/', views.generate_schedule, name = 'generate_schedule'),
    path('generate/',views.generate, name='generate'),
    path('generate_exam_schedule/', views.generate_exam_schedule, name = 'generate_exam_schedule'),
    path('accept_schedule/', views.accept_schedule, name='accept_schedule'),
    path('accept_exam_schedule/', views.accept_exam_schedule, name='accept_exam_schedule'),
]
