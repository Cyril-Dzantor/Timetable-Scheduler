from django.shortcuts import render,redirect
from django.contrib.auth import logout

from Timetable.models import Course, Lecturer, Class, Room
from Scheduler.models import LectureSchedule, ExamSchedule, StudentExamAllocation

def home(request):
    context = {
        'course_count': Course.objects.count(),
        'lecturer_count': Lecturer.objects.count(),
        'class_count': Class.objects.count(),
        'room_count': Room.objects.count(),
        'lecture_schedule_count': LectureSchedule.objects.count(),
        'exam_schedule_count': ExamSchedule.objects.count(),
        'student_exam_allocation_count': StudentExamAllocation.objects.count(),
    }
    return render(request, 'home/home.html', context)

# # Create your views here.
# def home(request):
#     return render(request, 'home/home.html')

def contact(request):
    return render(request,'home/contact.html')

def about(request):
    return render(request, 'home/about.html')

def logout_view(request):
    logout(request)
    return redirect('login')