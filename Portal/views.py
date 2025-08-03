from django.shortcuts import render,redirect 
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from Scheduler.models import LectureSchedule, ExamSchedule
from Timetable.models import TimeSlot, Class, Lecturer, Course,ExamDate
from collections import defaultdict
from Users.models import StudentProfile
from django.db.models import Q
from django.contrib import messages

from datetime import datetime

@login_required
def student_dashboard(request):
    # Get the current student's department and level (you'll need to adjust this based on your model)
    student = request.user.student_profile  # Assuming you have a Student model linked to User
    
    # Check if class timetable exists for this student's department and level
    class_timetable_exists = LectureSchedule.objects.exists()
    
    # Check if exam timetable exists
    exam_timetable_exists = ExamSchedule.objects.exists()
    
    context = {
        'class_timetable': class_timetable_exists,
        'exam_timetable': exam_timetable_exists,
    }
    return render(request, 'portal/student_dashboard.html', context)

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


@login_required
def timetable_grid(request):
    """
    Display filtered timetable grid based on user type
    """
    user = request.user
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Get all time slots for the grid (lecture slots only)
    time_slots = TimeSlot.objects.filter(is_lecture_slot=True).order_by('start_time')
    
    # Get filter parameters
    selected_class = request.GET.get('class_filter', '')
    selected_lecturer = request.GET.get('lecturer_filter', '')
    selected_course = request.GET.get('course_filter', '')
    
    # Get all available classes and lecturers for filter dropdowns
    all_classes = Class.objects.all().order_by('code')
    all_lecturers = Lecturer.objects.filter(is_active=True).order_by('name')
    all_courses = Course.objects.all().order_by('code')
    
    # Base query for schedules
    schedules = LectureSchedule.objects.all().select_related(
        'course', 'assigned_class', 'lecturer', 'room', 'time_slot'
    ).prefetch_related('course__students')
    
    # Apply role-based filtering
    if user.is_student and hasattr(user, 'student_profile'):
        # STUDENT VIEW: Filter by registered courses and class
        student_profile = user.student_profile
        registered_courses = student_profile.registered_courses.all()
        student_class = student_profile.class_code  # Get the student's class from their profile
        
        if registered_courses.exists():
            schedules = schedules.filter(
                course__in=registered_courses,
                assigned_class__code=student_class  # Filter by student's class
            )
            print(f"Showing timetable for student {user.email} - Registered courses: {[c.code for c in registered_courses]}, Class: {student_class}")
        else:
            messages.warning(request, "You haven't registered for any courses yet.")
            schedules = schedules.none()
            
    elif user.is_lecturer:
        # LECTURER VIEW: Get the related Lecturer instance
        try:
            lecturer = user.timetable_lecturer  # Using the OneToOneField from Lecturer model
            if lecturer:
                schedules = schedules.filter(lecturer=lecturer)
                print(f"Showing timetable for lecturer {user.email}")
            else:
                messages.error(request, "Lecturer record not found")
                schedules = schedules.none()
        except Exception as e:
            messages.error(request, f"Error accessing lecturer data: {str(e)}")
            schedules = schedules.none()
            
    elif user.is_admin:
        # ADMIN VIEW: Show all schedules (with optional filters)
        print(f"Admin view - showing all schedules")
        
    # Apply additional filters (for admin or when manually selected)
    if selected_course and (user.is_admin or not user.is_student):
        schedules = schedules.filter(course__code=selected_course)
    
    if selected_class and (user.is_admin or not user.is_student):
        schedules = schedules.filter(assigned_class__code=selected_class)
    
    if selected_lecturer and (user.is_admin or not user.is_lecturer):
        schedules = schedules.filter(lecturer__name=selected_lecturer)
    
    # Create grid data structure
    grid_data = defaultdict(lambda: defaultdict(list))
    
    # Organize schedules into grid format
    for schedule in schedules:
        day = schedule.day
        time_slot = schedule.time_slot
        
        grid_data[day][time_slot.id].append({
            'id': schedule.id,
            'course_code': schedule.course.code,
            'course_title': schedule.course.title,
            'room_code': schedule.room.code,
            'lecturer_name': schedule.lecturer.name,
            'class_code': schedule.assigned_class.code,
            'time_display': f"{time_slot.start_time.strftime('%H:%M')} - {time_slot.end_time.strftime('%H:%M')}",
            'conflicts': check_schedule_conflicts(schedule)
        })

    # Determine base template based on user role
    base_template = 'home/base.html' if (user.is_superuser or user.is_admin) else 'portal/base.html'
    
    context = {
        'days': days,
        'time_slots': time_slots,
        'grid_data': dict(grid_data),
        'user_type': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin',
        'all_classes': all_classes,
        'all_lecturers': all_lecturers,
        'all_courses': all_courses,
        'selected_class': selected_class,
        'selected_lecturer': selected_lecturer,
        'selected_course': selected_course,
        'base_template': base_template
    }
    
    return render(request, 'portal/timetable_grid.html', context)

@login_required
def student_timetable(request):
    """
    Student-specific timetable view
    """
    return timetable_grid(request)

@login_required
def lecturer_timetable(request):
    """
    Lecturer-specific timetable view
    """
    return timetable_grid(request)

@login_required
def exam_timetable_grid(request):
    """
    Fully working exam timetable grid view with proper date handling
    """
    user = request.user
    
    # 1. GET ALL NECESSARY DATA
    # Get all distinct exam dates from ExamSchedule (not ExamDate)
    exam_dates = ExamSchedule.objects.dates('date', 'day').distinct().order_by('date')
    date_strings = [date.strftime('%Y-%m-%d') for date in exam_dates]
    day_names = [date.strftime('%A') for date in exam_dates]
    
    # Get all time slots marked as exam slots
    exam_time_slots = TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time')
    
    # Get all classes and courses for filters
    all_classes = Class.objects.all().order_by('code')
    all_courses = Course.objects.all().order_by('code')
    
    # 2. HANDLE FILTERS
    selected_class = request.GET.get('class_filter', '')
    selected_date_str = request.GET.get('date_filter', '')
    selected_course = request.GET.get('course_filter', '')
    
    # Initialize base query
    exam_schedules = ExamSchedule.objects.select_related(
        'course', 'time_slot'
    ).prefetch_related(
        'room_assignments',
        'room_assignments__room'
    )
    
    # 3. APPLY ROLE-BASED FILTERING
    if user.is_student and hasattr(user, 'student_profile'):
        registered_courses = user.student_profile.registered_courses.all()
        if registered_courses.exists():
            exam_schedules = exam_schedules.filter(course__in=registered_courses)
        else:
            messages.warning(request, "You haven't registered for any courses yet")
            exam_schedules = exam_schedules.none()
    
    elif user.is_lecturer and hasattr(user, 'timetable_lecturer'):
        exam_schedules = exam_schedules.filter(course__lecturers=user.timetable_lecturer)
    
    # 4. APPLY ADDITIONAL FILTERS
    if selected_course:
        exam_schedules = exam_schedules.filter(course__code=selected_course)
    
    if selected_class:
        class_obj = Class.objects.filter(code=selected_class).first()
        if class_obj:
            exam_schedules = exam_schedules.filter(
                Q(course__in=class_obj.courses.all()) |
                Q(room_assignments__classassignment__class_assigned=class_obj)
            ).distinct()
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            exam_schedules = exam_schedules.filter(date=selected_date)
        except ValueError:
            messages.error(request, "Invalid date format")
    
    # 5. BUILD GRID DATA STRUCTURE
    grid_data = defaultdict(lambda: defaultdict(list))
    
    for exam in exam_schedules:
        exam_date_str = exam.date.strftime('%Y-%m-%d')
        
        # Only include if date is in our exam dates
        if exam_date_str in date_strings:
            time_slot = exam.time_slot
            
            # Get room info
            rooms = []
            for room_assignment in exam.room_assignments.all():
                rooms.append({
                    'room_code': room_assignment.room.code,
                    'room_type': getattr(room_assignment.room.room_type, 'name', 'N/A'),
                    'capacity': getattr(room_assignment.room, 'capacity', 0)
                })
            
            if not rooms:
                rooms = [{'room_code': 'TBA', 'room_type': 'N/A', 'capacity': 0}]
            
            # Add to grid
            grid_data[exam_date_str][time_slot.id].append({
                'course_code': exam.course.code,
                'course_title': exam.course.title,
                'date': exam.date,
                'time_display': f"{time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}",
                'duration': getattr(time_slot, 'duration', 'N/A'),
                'rooms': rooms
            })
    
    # 6. DETERMINE BASE TEMPLATE (using your original logic)
    if user.is_authenticated:
        if user.is_student:
            base_template = 'portal/base.html'
        elif user.is_lecturer:
            base_template = 'portal/base.html'
        else:
            base_template = 'home/base.html'
    else:
        base_template = 'home/home.html'
    
    # 7. PREPARE CONTEXT
    context = {
        'days': day_names,  # For column headers ('Monday', 'Tuesday')
        'dates': date_strings,  # Actual dates ('2023-12-25')
        'time_slots': exam_time_slots,
        'grid_data': dict(grid_data),
        'all_classes': all_classes,
        'all_courses': all_courses,
        'exam_dates': exam_dates,
        'selected_class': selected_class,
        'selected_date': selected_date_str,
        'selected_course': selected_course,
        'base_template': base_template,
        'user_type': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin'
    }
    
    return render(request, 'portal/exam_timetable_grid.html', context)


def check_schedule_conflicts(schedule):
    """Check if this schedule has any conflicts"""
    conflicts = []
    
    # Check room conflicts
    room_conflicts = LectureSchedule.objects.filter(
        day=schedule.day,
        time_slot=schedule.time_slot,
        room=schedule.room
    ).exclude(id=schedule.id)
    
    if room_conflicts.exists():
        conflicts.append(f"Room conflict with {room_conflicts.first().course.code}")
    
    # Check lecturer conflicts
    lecturer_conflicts = LectureSchedule.objects.filter(
        day=schedule.day,
        time_slot=schedule.time_slot,
        lecturer=schedule.lecturer
    ).exclude(id=schedule.id)
    
    if lecturer_conflicts.exists():
        conflicts.append(f"Lecturer conflict with {lecturer_conflicts.first().course.code}")
    
    return conflicts