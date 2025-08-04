# portal/urls.py
from django.urls import path
from . import views
from .views import (
    timetable_view,
    add_event,
    edit_event,
    delete_event,
    timetable_settings,
    day_view,
    student_exam_schedule_list
)
app_name = 'portal'

urlpatterns = [
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('lecturer-dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('profile/', views.portal_profile, name='portal_profile'), 
    path('portal_home',views.portal_home, name='portal_home'),
    path('timetable/', views.timetable_grid, name='timetable_grid'),
    path('student-timetable/', views.student_timetable, name='student_timetable'),
    path('lecturer-timetable/', views.lecturer_timetable, name='lecturer_timetable'),
    path('exam-timetable/', views.exam_timetable_grid, name='exam_timetable_grid'),

    path('exam-schedule/list/', student_exam_schedule_list, name='exam_schedule_list'),

    path('personal_timetable/', timetable_view, name='timetable'),
    path('personal_timetable/add/', add_event, name='add_event'),
    path('personal_timetable/edit/<int:event_id>/', edit_event, name='edit_event'),
    path('personal_timetable/delete/<int:event_id>/', delete_event, name='delete_event'),
    path('personal_timetable/settings/', timetable_settings, name='timetable_settings'),
    path('personal_timetable/day/', day_view, name='day_view'),
    path('personal_timetable/day/<str:date_string>/', day_view, name='day_view_with_date'),
]
