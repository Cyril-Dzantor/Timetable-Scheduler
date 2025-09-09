from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from Scheduler.models import LectureSchedule, ExamSchedule
from Timetable.models import TimeSlot, Class, Lecturer, Course,ExamDate,Room 
from collections import defaultdict
from Users.models import StudentProfile
from django.db.models import Q
from django.contrib import messages
from django.db.models import Prefetch


from datetime import datetime,timedelta
from django.utils import timezone

from .models import PersonalEvent, PersonalTimetable, PersonalEventType
from Scheduler.models import ExamRoomAssignment,ExamRoomClassAllocation,StudentExamAllocation
from .forms import PersonalEventForm, TimetableSettingsForm

from Users.models import User

@login_required
def student_dashboard(request):
    student = request.user.student_profile
    
    # Check if class timetable exists for this student's class_code
    class_timetable_exists = LectureSchedule.objects.filter(
        assigned_class__code=student.class_code
    ).exists()
    
    # Check if exam timetable exists for the student's registered courses
    exam_timetable_exists = ExamSchedule.objects.filter(
        course__in=student.registered_courses.all()
    ).exists()
    
    context = {
        'class_timetable_exists': class_timetable_exists,
        'exam_timetable_exists': exam_timetable_exists,
    }
    return render(request, 'portal/student_dashboard.html', context)



@login_required
def lecturer_dashboard(request):
    # Get the Lecturer instance associated with this user
    try:
        lecturer = Lecturer.objects.get(user=request.user)
    except Lecturer.DoesNotExist:
        lecturer = None
    
    # Check for lectures
    lectures_exist = LectureSchedule.objects.filter(
        lecturer=lecturer
    ).exists() if lecturer else False
    
    # Check for exam duties
    exams_exist = ExamRoomAssignment.objects.filter(
        proctors=lecturer
    ).exists() if lecturer else False
    
    context = {
        'lectures': lectures_exist,
        'exams': exams_exist,
    }
    return render(request, "portal/lecturer_dashboard.html", context)

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
    
    # We'll derive time slots from the filtered LectureSchedule below to ensure
    # we only show slots that actually have schedules.
    time_slots = TimeSlot.objects.none()
    
    # Get filter parameters
    selected_class = request.GET.get('class_filter', '')
    selected_lecturer = request.GET.get('lecturer_filter', '')
    selected_course = request.GET.get('course_filter', '')
    selected_room = request.GET.get('room_filter', '')  # Add room filter
    
    # Get all available classes, lecturers, courses, and rooms for filter dropdowns
    all_classes = Class.objects.all().order_by('code')
    all_lecturers = Lecturer.objects.filter(is_active=True).order_by('name')
    all_courses = Course.objects.all().order_by('code')
    all_rooms = Room.objects.all().order_by('code')  # Add rooms query
    
    # Base query for schedules
    schedules = LectureSchedule.objects.all().select_related(
        'course', 'assigned_class', 'lecturer', 'room', 'time_slot'
    ).prefetch_related('course__students')
    
    # Apply role-based filtering
    if user.is_student and hasattr(user, 'student_profile'):
        # STUDENT VIEW: Filter by registered courses and class
        student_profile = user.student_profile
        registered_courses = student_profile.registered_courses.all()
        student_class = student_profile.class_code
        
        if registered_courses.exists():
            schedules = schedules.filter(
                course__in=registered_courses,
                assigned_class__code=student_class
            )
        else:
            messages.warning(request, "You haven't registered for any courses yet.")
            schedules = schedules.none()
            
    elif user.is_lecturer:
        # LECTURER VIEW: Get the related Lecturer instance
        try:
            lecturer = user.timetable_lecturer
            if lecturer:
                schedules = schedules.filter(lecturer=lecturer)
            else:
                messages.error(request, "Lecturer record not found")
                schedules = schedules.none()
        except Exception as e:
            messages.error(request, f"Error accessing lecturer data: {str(e)}")
            schedules = schedules.none()
            
    # Apply additional filters (for admin or when manually selected)
    if selected_course and (user.is_admin or not user.is_student):
        schedules = schedules.filter(course__code=selected_course)
    
    if selected_class and (user.is_admin or not user.is_student):
        schedules = schedules.filter(assigned_class__code=selected_class)
    
    if selected_lecturer and (user.is_admin or not user.is_lecturer):
        schedules = schedules.filter(lecturer__name=selected_lecturer)
    
    if selected_room:  # Add room filter
        schedules = schedules.filter(room__code=selected_room)
    
    # Now derive time slots from the filtered schedules so the grid shows
    # only slots that actually have LectureSchedule entries
    time_slots = TimeSlot.objects.filter(
        id__in=schedules.values_list('time_slot_id', flat=True).distinct()
    ).order_by('start_time')

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
        'all_rooms': all_rooms,  # Add to context
        'selected_class': selected_class,
        'selected_lecturer': selected_lecturer,
        'selected_course': selected_course,
        'selected_room': selected_room,  # Add to context
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


# @login_required
# def exam_timetable_grid(request):
#     """
#     Exam timetable grid view with support for teaching vs proctoring views
#     """
#     user = request.user
    
#     # Get all distinct exam dates
#     exam_dates = ExamSchedule.objects.dates('date', 'day').distinct().order_by('date')
#     date_strings = [date.strftime('%Y-%m-%d') for date in exam_dates]
#     day_names = [date.strftime('%A') for date in exam_dates]
    
#     # Get all time slots marked as exam slots
#     exam_time_slots = TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time')
    
#     # Get all classes, courses, and rooms for filters
#     all_classes = Class.objects.all().order_by('code')
#     all_courses = Course.objects.all().order_by('code')
#     all_rooms = Room.objects.all().order_by('code')
    
#     # Handle filters
#     selected_class = request.GET.get('class_filter', '')
#     selected_date_str = request.GET.get('date_filter', '')
#     selected_course = request.GET.get('course_filter', '')
#     selected_room = request.GET.get('room_filter', '')
#     view_type = request.GET.get('view_type', 'teaching')  # Default to teaching view
    
#     # Initialize base query
#     exam_schedules = ExamSchedule.objects.select_related(
#         'course', 'time_slot'
#     ).prefetch_related(
#         'room_assignments',
#         'room_assignments__room'
#     )
    
#     # Apply role-based filtering
#     if user.is_student and hasattr(user, 'student_profile'):
#         registered_courses = user.student_profile.registered_courses.all()
#         exam_schedules = exam_schedules.filter(course__in=registered_courses) if registered_courses.exists() else exam_schedules.none()
    
#     elif user.is_lecturer and hasattr(user, 'lecturer_profile'):
#         if view_type == 'proctoring':
#             # Only show rooms where this lecturer is proctoring
#             exam_schedules = exam_schedules.filter(
#                 room_assignments__proctors__user=user
#             ).distinct()
#         else:
#             # Default to teaching exams
#             exam_schedules = exam_schedules.filter(course__lecturers__user=user)
    
#     # Apply additional filters
#     if selected_course:
#         exam_schedules = exam_schedules.filter(course__code=selected_course)
    
#     if selected_class:
#         class_obj = Class.objects.filter(code=selected_class).first()
#         if class_obj:
#             exam_schedules = exam_schedules.filter(
#                 Q(course__in=class_obj.courses.all()) |
#                 Q(room_assignments__class_allocations__class_assigned=class_obj)
#             ).distinct()
    
#     if selected_date_str:
#         try:
#             selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
#             exam_schedules = exam_schedules.filter(date=selected_date)
#         except ValueError:
#             messages.error(request, "Invalid date format")

#     if selected_room:
#         exam_schedules = exam_schedules.filter(room_assignments__room__code=selected_room).distinct()
    
#     # Build grid data structure
#     grid_data = defaultdict(lambda: defaultdict(list))
    
#     for exam in exam_schedules:
#         exam_date_str = exam.date.strftime('%Y-%m-%d')
        
#         if exam_date_str in date_strings:
#             time_slot = exam.time_slot
            
#             # Get only the rooms where current user is proctoring (for proctoring view)
#             rooms = []
#             for room_assignment in exam.room_assignments.all():
#                 if view_type == 'proctoring':
#                     # Only include if current user is a proctor for this room
#                     if room_assignment.proctors.filter(user=user).exists():
#                         rooms.append({
#                             'room_code': room_assignment.room.code,
#                             'room_type': getattr(room_assignment.room.room_type, 'name', 'N/A'),
#                             'capacity': getattr(room_assignment.room, 'capacity', 0)
#                         })
#                 else:
#                     # For teaching view, show all rooms
#                     rooms.append({
#                         'room_code': room_assignment.room.code,
#                         'room_type': getattr(room_assignment.room.room_type, 'name', 'N/A'),
#                         'capacity': getattr(room_assignment.room, 'capacity', 0)
#                     })
            
#             if not rooms:
#                 rooms = [{'room_code': 'TBA', 'room_type': 'N/A', 'capacity': 0}]
            
#             grid_data[exam_date_str][time_slot.id].append({
#                 'course_code': exam.course.code,
#                 'course_title': exam.course.title,
#                 'date': exam.date,
#                 'time_display': f"{time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}",
#                 'duration': getattr(time_slot, 'duration', 'N/A'),
#                 'rooms': rooms,
#                 # Don't include invigilators list for proctoring view since it's just the current user
#                 'is_proctoring': view_type == 'proctoring'
#             })
    
#     # Determine base template
#     if user.is_authenticated:
#         if user.is_student:
#             base_template = 'portal/base.html'
#         elif user.is_lecturer:
#             base_template = 'portal/base.html'
#         else:
#             base_template = 'home/base.html'
    
#     context = {
#         'days': day_names,
#         'dates': date_strings,
#         'time_slots': exam_time_slots,
#         'grid_data': dict(grid_data),
#         'all_classes': all_classes,
#         'all_courses': all_courses,
#         'all_rooms': all_rooms,
#         'exam_dates': exam_dates,
#         'selected_class': selected_class,
#         'selected_date': selected_date_str,
#         'selected_course': selected_course,
#         'selected_room': selected_room,
#         'view_type': view_type,
#         'base_template': base_template,
#         'user_type': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin'
#     }
    
#     return render(request, 'portal/exam_timetable_grid.html', context)

@login_required
def exam_timetable_grid(request):
    """
    Exam timetable grid view with support for teaching vs proctoring views
    """
    user = request.user
    
    # Get all distinct exam dates
    exam_dates = ExamSchedule.objects.dates('date', 'day').distinct().order_by('date')
    date_strings = [date.strftime('%Y-%m-%d') for date in exam_dates]
    day_names = [date.strftime('%A') for date in exam_dates]
    
    # Get all time slots marked as exam slots
    exam_time_slots = TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time')
    
    # Get all classes, courses, and rooms for filters
    all_classes = Class.objects.all().order_by('code')
    all_courses = Course.objects.all().order_by('code')
    all_rooms = Room.objects.all().order_by('code')
    
    # Handle filters
    selected_class = request.GET.get('class_filter', '')
    selected_date_str = request.GET.get('date_filter', '')
    selected_course = request.GET.get('course_filter', '')
    selected_room = request.GET.get('room_filter', '')
    view_type = request.GET.get('view_type', 'teaching')  # Default to teaching view
    
    # Initialize base query - ADD prefetch_related for proctors
    exam_schedules = ExamSchedule.objects.select_related(
        'course', 'time_slot'
    ).prefetch_related(
        'room_assignments',
        'room_assignments__room',
        'room_assignments__proctors'  # ADD THIS
    )
    
    # Apply role-based filtering
    if user.is_student and hasattr(user, 'student_profile'):
        registered_courses = user.student_profile.registered_courses.all()
        exam_schedules = exam_schedules.filter(course__in=registered_courses) if registered_courses.exists() else exam_schedules.none()
    
    elif user.is_lecturer and hasattr(user, 'lecturer_profile'):
        if view_type == 'proctoring':
            # Only show rooms where this lecturer is proctoring
            exam_schedules = exam_schedules.filter(
                room_assignments__proctors__user=user
            ).distinct()
        else:
            # Default to teaching exams
            exam_schedules = exam_schedules.filter(course__lecturers__user=user)
    
    # Apply additional filters
    if selected_course:
        exam_schedules = exam_schedules.filter(course__code=selected_course)
    
    if selected_class:
        class_obj = Class.objects.filter(code=selected_class).first()
        if class_obj:
            exam_schedules = exam_schedules.filter(
                Q(course__in=class_obj.courses.all()) |
                Q(room_assignments__class_allocations__class_assigned=class_obj)
            ).distinct()
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            exam_schedules = exam_schedules.filter(date=selected_date)
        except ValueError:
            messages.error(request, "Invalid date format")

    if selected_room:
        exam_schedules = exam_schedules.filter(room_assignments__room__code=selected_room).distinct()
    
    grid_data = defaultdict(lambda: defaultdict(list))
    
    for exam in exam_schedules:
        exam_date_str = exam.date.strftime('%Y-%m-%d')
        
        if exam_date_str in date_strings:
            time_slot = exam.time_slot
            
            # Get only the rooms where current user is proctoring (for proctoring view)
            rooms = []
            for room_assignment in exam.room_assignments.all():
                if view_type == 'proctoring':
                    # Only include if current user is a proctor for this room
                    if room_assignment.proctors.filter(user=user).exists():
                        rooms.append({
                            'room_code': room_assignment.room.code,
                            'room_type': getattr(room_assignment.room.room_type, 'name', 'N/A'),
                            'capacity': getattr(room_assignment.room, 'capacity', 0)
                        })
                else:
                    # For teaching view, show all rooms
                    rooms.append({
                        'room_code': room_assignment.room.code,
                        'room_type': getattr(room_assignment.room.room_type, 'name', 'N/A'),
                        'capacity': getattr(room_assignment.room, 'capacity', 0)
                    })
            
            if not rooms:
                rooms = [{'room_code': 'TBA', 'room_type': 'N/A', 'capacity': 0}]
            
            grid_data[exam_date_str][time_slot.id].append({
                'exam': exam,  
                'exam_id': exam.id,  
                'course_code': exam.course.code,
                'course_title': exam.course.title,
                'date': exam.date,
                'time_display': f"{time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}",
                'duration': getattr(time_slot, 'duration', 'N/A'),
                'rooms': rooms,
                'is_proctoring': view_type == 'proctoring'
            })
    
    # Determine base template
    if user.is_authenticated:
        if user.is_student:
            base_template = 'portal/base.html'
        elif user.is_lecturer:
            base_template = 'portal/base.html'
        else:
            base_template = 'home/base.html'
    else:
        base_template = 'home/base.html'
    
    context = {
        'days': day_names,
        'dates': date_strings,
        'time_slots': exam_time_slots,
        'grid_data': dict(grid_data),
        'all_classes': all_classes,
        'all_courses': all_courses,
        'all_rooms': all_rooms,
        'exam_dates': exam_dates,
        'selected_class': selected_class,
        'selected_date': selected_date_str,
        'selected_course': selected_course,
        'selected_room': selected_room,
        'view_type': view_type,
        'base_template': base_template,
        'user_type': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin',
        'exam_schedules': exam_schedules  
    }
    
    return render(request, 'portal/exam_timetable_grid.html', context)


@login_required
def exam_schedule_list_all(request):
    """
    Role-aware exam list view for Students, Lecturers, and Admins.
    Reuses the student layout idea but broadens data per role.
    """
    user = request.user
    exams_qs = ExamSchedule.objects.select_related('course', 'time_slot').prefetch_related(
        Prefetch('room_assignments', queryset=ExamRoomAssignment.objects.select_related('room__building__college')
                 .prefetch_related('class_allocations'))
    ).order_by('date', 'time_slot__start_time').distinct()

    # Role scoping
    if user.is_student and hasattr(user, 'student_profile'):
        registered = user.student_profile.registered_courses.all()
        student_class = user.student_profile.class_code
        exams_qs = exams_qs.filter(course__in=registered)
    elif user.is_lecturer and hasattr(user, 'lecturer_profile'):
        exams_qs = exams_qs.filter(
            Q(course__lecturers__user=user) |
            Q(room_assignments__proctors__user=user)
        ).distinct()
    elif user.is_admin and hasattr(user, 'admin_profile') and user.admin_profile.college_id:
        exams_qs = exams_qs.filter(room_assignments__room__building__college=user.admin_profile.college).distinct()

    # Build list items
    items = []
    for exam in exams_qs:
        start_time = exam.time_slot.start_time
        end_time = exam.time_slot.end_time
        duration_minutes = (end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute)
        rooms = []
        total_enrollment = 0
        
        for ra in exam.room_assignments.all():
            college = getattr(getattr(getattr(ra.room, 'building', None), 'college', None), 'name', None)
            
            # Calculate enrollment for this room
            room_enrollment = 0
            for class_allocation in ra.class_allocations.all():
                room_enrollment += class_allocation.student_count
            
            total_enrollment += room_enrollment
            
            rooms.append({
                'code': ra.room.code,
                'building': getattr(ra.room.building, 'name', 'N/A'),
                'college': college or 'College Not Specified',
                'enrollment': room_enrollment,
            })

        items.append({
            'exam_id': exam.id,
            'course_code': exam.course.code,
            'course_title': exam.course.title,
            'date': exam.date,
            'day': exam.date.strftime('%A'),
            'start_time': start_time.strftime('%H:%M'),
            'end_time': end_time.strftime('%H:%M'),
            'duration': f"{duration_minutes} minutes",
            'rooms': rooms or [{'code': 'TBA', 'building': 'To be announced', 'college': 'College Not Specified', 'enrollment': 0}],
            'total_enrollment': total_enrollment,
        })

    if user.is_authenticated:
        if user.is_student:
            base_template = 'portal/base.html'
        elif user.is_lecturer:
            base_template = 'portal/base.html'
        else:
            base_template = 'home/base.html'
    else:
        base_template = 'home/base.html'
    return render(request, 'portal/exam_schedule_list_all.html', {
        'items': items,
        'base_template': base_template,
        'role': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin'
    })


@login_required
def timetable_list_view(request):
    """Role-aware list view for the normal lecture timetable."""
    user = request.user
    schedules = LectureSchedule.objects.select_related('course', 'time_slot', 'room', 'assigned_class', 'lecturer')

    if user.is_student and hasattr(user, 'student_profile'):
        registered = user.student_profile.registered_courses.all()
        class_code = user.student_profile.class_code
        schedules = schedules.filter(course__in=registered, assigned_class__code=class_code)
    elif user.is_lecturer and hasattr(user, 'timetable_lecturer') and user.timetable_lecturer:
        schedules = schedules.filter(lecturer=user.timetable_lecturer)
    elif user.is_admin:
        # optional: keep as all; could filter by admin college if modeled
        pass

    # Sort schedules properly: by class, then course, then day, then time
    items = []
    for s in schedules.order_by('assigned_class__code', 'course__code', 'day', 'time_slot__start_time'):
        start = s.time_slot.start_time.strftime('%H:%M')
        end = s.time_slot.end_time.strftime('%H:%M')
        items.append({
            'schedule_id': s.id,
            'course_code': s.course.code,
            'course_title': s.course.title,
            'day': s.day,
            'start_time': start,
            'end_time': end,
            'room': getattr(s.room, 'code', 'TBA'),
            'class_code': getattr(s.assigned_class, 'code', ''),
            'lecturer': getattr(s.lecturer, 'name', ''),
            'enrollment': getattr(s, 'enrollment', 0),
        })

    if user.is_authenticated:
        if user.is_student:
            base_template = 'portal/base.html'
        elif user.is_lecturer:
            base_template = 'portal/base.html'
        else:
            base_template = 'home/base.html'
    else:
        base_template = 'home/base.html'
    return render(request, 'portal/timetable_list.html', {
        'items': items,
        'base_template': base_template,
        'role': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin'
    })
@login_required
def student_exam_schedule_list(request):
    """
    Student-specific exam timetable in list view format showing only the room
    where the student has been specifically assigned
    """
    user = request.user
    
    if not (user.is_student and hasattr(user, 'student_profile')):
        messages.error(request, "This view is only available to students")
        return redirect('portal:portal_home')
    
    # Get student's profile information
    student_profile = user.student_profile
    student_index = student_profile.index_number
    student_class = student_profile.class_code
    
    # Get exam schedules with building and college data
    exam_schedules = ExamSchedule.objects.filter(
        course__in=student_profile.registered_courses.all()
    ).select_related(
        'course', 'time_slot'
    ).prefetch_related(
        Prefetch('room_assignments',
                queryset=ExamRoomAssignment.objects.select_related(
                    'room__building__college'  # Fetch building and college
                )
                .prefetch_related(
                    Prefetch('class_allocations',
                            queryset=ExamRoomClassAllocation.objects.filter(
                                class_assigned__code=student_class
                            )
                    )
                )
        )
    ).order_by('date', 'time_slot__start_time').distinct()
    
    # Get student allocations with building and college data
    student_allocations = {
        alloc.exam_id: alloc 
        for alloc in StudentExamAllocation.objects.filter(
            student_index=student_index,
            exam__in=[exam.id for exam in exam_schedules]
        ).select_related(
            'room__building__college'  # Fetch building and college
        )
    }
    
    # Prepare exam data
    exams = []
    for exam in exam_schedules:
        # Calculate duration
        start_time = exam.time_slot.start_time
        end_time = exam.time_slot.end_time
        duration_minutes = (end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute)
        duration = f"{duration_minutes} minutes"
        
        # Get student's specific allocation
        allocation = student_allocations.get(exam.id)
        
        rooms = []
        if allocation:
            # Student has specific room assignment
            room = allocation.room
            college = getattr(room.building.college, 'name', None) if hasattr(room, 'building') else None
            
            rooms.append({
                'code': room.code,
                'building': getattr(room.building, 'name', 'N/A'),
                'college': college or "College Not Specified",  # Actual college name
                'seat_info': f"Column {allocation.column_number}",
                'is_assigned': True
            })
        else:
            # Fallback to class allocation
            for room_assignment in exam.room_assignments.all():
                for alloc in room_assignment.class_allocations.all():
                    if alloc.class_assigned.code == student_class:
                        seat_info = f"Columns: {alloc.columns_used}" if alloc.columns_used else ""
                        building = getattr(room_assignment, 'room', None)
                        college = getattr(building.building.college, 'name', None) if building else None
                        
                        rooms.append({
                            'code': room_assignment.room.code,
                            'building': getattr(room_assignment.room.building, 'name', 'N/A'),
                            'college': college or "College Not Specified",  # Actual college name
                            'seat_info': seat_info,
                            'is_assigned': False
                        })
                        break
        
        exams.append({
            'course_code': exam.course.code,
            'course_title': exam.course.title,
            'date': exam.date,
            'day': exam.date.strftime('%A'),
            'start_time': start_time.strftime('%H:%M'),
            'end_time': end_time.strftime('%H:%M'),
            'duration': duration,
            'rooms': rooms if rooms else [{
                'code': 'TBA', 
                'building': 'To be announced', 
                'college': "College Not Specified",
                'seat_info': '', 
                'is_assigned': False
            }]
        })

    if user.is_authenticated:
        if user.is_student:
            base_template = 'portal/base.html'
        elif user.is_lecturer:
            base_template = 'portal/base.html'
        else:
            base_template = 'home/base.html'
    else:
        base_template = 'home/base.html'
    
    context = {
        'exams': exams,
        'base_template': base_template,
        'student_name': user.get_full_name() or user.username,
        'student_class': student_class,
        'student_index': student_index,
        'current_year': f"{datetime.now().year}/{datetime.now().year + 1}"
    }
    
    return render(request, 'portal/exam_schedule_list.html', context)


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





@login_required
def timetable_view(request):
    timetable, _ = PersonalTimetable.objects.get_or_create(user=request.user)
    view = request.GET.get('view', timetable.default_view)
    
    if view == 'day':
        current_date = timezone.now().date()
        return redirect('portal:day_view_with_date', date_string=current_date.strftime('%Y-%m-%d'))
    
    # Week view logic
    events = PersonalEvent.objects.filter(user=request.user)
    institutional_events = []
    exam_events = []
    
    if timetable.show_institutional_classes:
        # For students
        if request.user.is_student and hasattr(request.user, 'student_profile'):
            student_profile = request.user.student_profile
            registered_courses = student_profile.registered_courses.all()
            student_class = student_profile.class_code
            
            if registered_courses.exists():
                institutional_events = LectureSchedule.objects.filter(
                    course__in=registered_courses,
                    assigned_class__code=student_class
                ).select_related('course', 'room', 'time_slot', 'assigned_class', 'lecturer')
            else:
                messages.warning(request, "You haven't registered for any courses yet.")
        
        # For lecturers
        elif request.user.is_lecturer and hasattr(request.user, 'timetable_lecturer'):
            lecturer = request.user.timetable_lecturer
            if lecturer:
                institutional_events = LectureSchedule.objects.filter(
                    lecturer=lecturer
                ).select_related('course', 'room', 'time_slot', 'assigned_class', 'lecturer')
            else:
                messages.error(request, "Lecturer record not found")
    
    if timetable.show_exams:
        # For students
        if request.user.is_student and hasattr(request.user, 'student_profile'):
            student_profile = request.user.student_profile
            registered_courses = student_profile.registered_courses.all()
            student_class = student_profile.class_code
            
            if registered_courses.exists():
                exam_events = ExamSchedule.objects.filter(
                    course__in=registered_courses,
                    course__classes__code=student_class
                ).select_related('course', 'time_slot')
        
        # For lecturers
        elif request.user.is_lecturer and hasattr(request.user, 'timetable_lecturer'):
            lecturer = request.user.timetable_lecturer
            if lecturer:
                exam_events = ExamSchedule.objects.filter(
                    course__lecturers=lecturer
                ).select_related('course', 'time_slot')
    
    context = {
        'timetable': timetable,
        'events': events,
        'institutional_events': institutional_events,
        'exam_events': exam_events,
        'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'time_slots': TimeSlot.objects.filter(is_lecture_slot=True).order_by('start_time'),
        'current_view': view,
        'today': timezone.now().strftime('%A'),
    }
    return render(request, 'portal/timetable.html', context)
    


@login_required
def add_event(request):
    if request.method == 'POST':
        form = PersonalEventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            messages.success(request, 'Event added successfully!')
            return redirect('portal:timetable')
    else:
        form = PersonalEventForm(user=request.user)
    
    return render(request, 'portal/event_form.html', {
        'form': form,
        'title': 'Add New Event'
    })

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(PersonalEvent, id=event_id, user=request.user)
    if request.method == 'POST':
        form = PersonalEventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('portal:timetable')
    else:
        form = PersonalEventForm(instance=event, user=request.user)
    
    return render(request, 'portal/event_form.html', {
        'form': form,
        'title': 'Edit Event'
    })

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(PersonalEvent, id=event_id, user=request.user)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
    return redirect('portal:timetable')

@login_required
def timetable_settings(request):
    timetable = get_object_or_404(PersonalTimetable, user=request.user)
    if request.method == 'POST':
        form = TimetableSettingsForm(request.POST, instance=timetable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated!')
            return redirect('portal:timetable')
    else:
        form = TimetableSettingsForm(instance=timetable)
    
    return render(request, 'portal/timetable_settings.html', {
        'form': form
    })



@login_required
def day_view(request, date_string=None):
    timetable, _ = PersonalTimetable.objects.get_or_create(user=request.user)
    
    try:
        if date_string:
            current_date = datetime.strptime(date_string, '%Y-%m-%d').date()
        else:
            current_date = timezone.now().date()
    except ValueError:
        current_date = timezone.now().date()
        return redirect('portal:day_view_with_date', date_string=current_date.strftime('%Y-%m-%d'))
    
    current_day = current_date.strftime('%A')
    prev_day = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
    next_day = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    events = PersonalEvent.objects.filter(user=request.user, day=current_day)
    institutional_events = []
    
    if timetable.show_institutional_classes:
        if hasattr(request.user, 'timetable_lecturer'):
            institutional_events = LectureSchedule.objects.filter(
                lecturer=request.user.timetable_lecturer,
                day=current_day
            ).select_related('course', 'room', 'time_slot')
        else:
            try:
                student_classes = request.user.student_classes.all()
                institutional_events = LectureSchedule.objects.filter(
                    assigned_class__in=student_classes,
                    day=current_day
                ).select_related('course', 'room', 'time_slot')
            except AttributeError:
                pass
    
    context = {
        'timetable': timetable,
        'events': events,
        'institutional_events': institutional_events,
        'time_slots': TimeSlot.objects.all().order_by('start_time'),
        'current_day': current_day,
        'current_date': current_date,
        'prev_day': prev_day,
        'next_day': next_day,
    }
    return render(request, 'portal/day_view.html', context)


    