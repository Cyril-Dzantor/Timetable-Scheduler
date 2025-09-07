from django.contrib import admin
from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    path('generate_schedule/', views.generate_schedule, name = 'generate_schedule'),
    path('generate/',views.generate, name='generate'),
    path('generate_exam_schedule/', views.generate_exam_schedule, name = 'generate_exam_schedule'),
    path('accept_schedule/', views.accept_schedule, name='accept_schedule'),
    path('accept_exam_schedule/', views.accept_exam_schedule, name='accept_exam_schedule'),
    
    path('edit-schedule/<int:schedule_id>/', views.edit_schedule, name='edit_schedule'),
    path('edit-exam-schedule/<int:exam_id>/', views.edit_exam_schedule, name='edit_exam_schedule'),

    path('delete-schedule/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('add-schedule/', views.add_schedule, name='add_schedule'),
    path('delete-exam-schedule/<int:exam_id>/', views.delete_exam_schedule, name='delete_exam_schedule'),
]

