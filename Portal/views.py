from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from Scheduler.models import LectureSchedule, ExamSchedule
from Timetable.models import TimeSlot, Class, Lecturer, Course
from Users.models import StudentProfile, LecturerProfile
from collections import defaultdict

def student_dashboard(request):
    return render(request, "portal/student_dashboard.html")

def lecturer_dashboard(request):
    return render(request, "portal/lecturer_dashboard.html")

@login_required
def portal_profile(request):
    return HttpResponse("This is your profile page.")

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
    
    # Get all available classes and lecturers for filter dropdowns
    all_classes = Class.objects.all().order_by('code')
    all_lecturers = Lecturer.objects.all().order_by('name')
    
    # Base query for schedules
    schedules = LectureSchedule.objects.all().select_related('course', 'assigned_class', 'lecturer', 'room', 'time_slot')
    
    # Apply role-based filtering
    if user.is_student and hasattr(user, 'student_profile') and user.student_profile.assigned_class:
        # Student: Show only their class's timetable
        student_class = user.student_profile.assigned_class
        schedules = schedules.filter(assigned_class=student_class)
        print(f"Filtering for student {user.email} - Class: {student_class.code}")
        
    elif user.is_lecturer and hasattr(user, 'lecturer_profile') and user.lecturer_profile.lecturer:
        # Lecturer: Show only their teaching schedule
        lecturer_obj = user.lecturer_profile.lecturer
        schedules = schedules.filter(lecturer=lecturer_obj)
        print(f"Filtering for lecturer {user.email} - Lecturer: {lecturer_obj.name}")
        
    elif user.is_admin:
        # Admin: Show all schedules (no filtering)
        print(f"Admin user {user.email} - Showing all schedules")
        
    # Apply additional filters (for admin users or when manually selected)
    if selected_class and (user.is_admin or not user.is_student):
        schedules = schedules.filter(assigned_class__code=selected_class)
    
    if selected_lecturer and (user.is_admin or not user.is_lecturer):
        schedules = schedules.filter(lecturer__name=selected_lecturer)
    
    # Create grid data structure
    grid_data = defaultdict(lambda: defaultdict(list))
    
    # Add lecture schedules
    for schedule in schedules:
        day = schedule.day
        time_slot = schedule.time_slot
        grid_data[day][time_slot.id].append({
            'course_code': schedule.course.code,
            'course_title': schedule.course.title,
            'room_code': schedule.room.code,
            'lecturer_name': schedule.lecturer.name,
            'class_code': schedule.assigned_class.code,
            'time_display': f"{time_slot.start_time.strftime('%H:%M')} - {time_slot.end_time.strftime('%H:%M')}"
        })
    
    context = {
        'days': days,
        'time_slots': time_slots,
        'grid_data': dict(grid_data),
        'user_type': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin',
        'all_classes': all_classes,
        'all_lecturers': all_lecturers,
        'selected_class': selected_class,
        'selected_lecturer': selected_lecturer
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
    Display exam timetable grid based on user type
    """
    user = request.user
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Get exam time slots for the grid
    exam_time_slots = TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time')
    
    # Get filter parameters
    selected_class = request.GET.get('class_filter', '')
    selected_date = request.GET.get('date_filter', '')
    
    # Get all available classes for filter dropdowns
    all_classes = Class.objects.all().order_by('code')
    
    # Get courses that are typically taken by each class
    # The system uses the proper Course-Class many-to-many relationship
    class_courses = {}
    for class_obj in all_classes:
        class_courses[class_obj.code] = list(class_obj.courses.values_list('code', flat=True))
    
    # Get unique exam dates for date filter
    exam_dates = ExamSchedule.objects.values_list('date', flat=True).distinct().order_by('date')
    
    # Base query for exam schedules with room assignments
    exam_schedules = ExamSchedule.objects.all().select_related('course', 'time_slot').prefetch_related(
        'room_assignments__room__room_type'
    )
    
    # Apply role-based filtering
    if user.is_student and hasattr(user, 'student_profile') and user.student_profile.assigned_class:
        # Student: Show only exams for their class's courses
        student_class = user.student_profile.assigned_class
        class_courses = student_class.courses.all()
        if class_courses.exists():
            exam_schedules = exam_schedules.filter(course__in=class_courses)
            print(f"Filtering exams for student {user.email} - Class: {student_class.code}, Courses: {[c.code for c in class_courses]}")
        else:
            print(f"Student {user.email} - Class {student_class.code} has no courses assigned")
            
    elif user.is_lecturer and hasattr(user, 'lecturer_profile') and user.lecturer_profile.lecturer:
        # Lecturer: Show only exams for courses they teach
        lecturer_obj = user.lecturer_profile.lecturer
        lecturer_courses = lecturer_obj.courses.all()
        if lecturer_courses.exists():
            exam_schedules = exam_schedules.filter(course__in=lecturer_courses)
            print(f"Filtering exams for lecturer {user.email} - Lecturer: {lecturer_obj.name}, Courses: {[c.code for c in lecturer_courses]}")
        else:
            print(f"Lecturer {user.email} - {lecturer_obj.name} has no courses assigned")
            
    elif user.is_admin:
        # Admin: Show all exams (no filtering)
        print(f"Admin user {user.email} - Showing all exams")
    
    # Debug: Print some information about the data
    print(f"Total exam schedules after role filtering: {exam_schedules.count()}")
    if selected_class:
        print(f"Selected class: {selected_class}")
        # Check if there are any class allocations for this class
        from Scheduler.models import ExamRoomClassAllocation
        class_allocations = ExamRoomClassAllocation.objects.filter(class_assigned__code=selected_class)
        print(f"Class allocations for {selected_class}: {class_allocations.count()}")
    
    # Apply additional filters (for admin users or when manually selected)
    if selected_class and (user.is_admin or not user.is_student):
        try:
            # Method 1: Use the proper Course-Class relationship
            selected_class_obj = Class.objects.get(code=selected_class)
            class_courses = selected_class_obj.courses.all()
            
            if class_courses.exists():
                # Filter exams by courses that this class takes
                exam_schedules = exam_schedules.filter(course__in=class_courses)
                print(f"Found {class_courses.count()} courses for class {selected_class}: {[c.code for c in class_courses]}")
            else:
                # Method 2: Fallback to ExamRoomClassAllocation (for exam-specific allocations)
                from Scheduler.models import ExamRoomClassAllocation
                class_allocations = ExamRoomClassAllocation.objects.filter(
                    class_assigned__code=selected_class
                ).values_list('room_assignment__exam_id', flat=True)
                
                if class_allocations.exists():
                    exam_schedules = exam_schedules.filter(id__in=class_allocations)
                    print(f"Found {class_allocations.count()} exam allocations for {selected_class}")
                else:
                    # Method 3: Fallback to course code matching (temporary)
                    class_course_codes = []
                    for exam in exam_schedules:
                        if selected_class.lower() in exam.course.code.lower():
                            class_course_codes.append(exam.course.code)
                    
                    if class_course_codes:
                        exam_schedules = exam_schedules.filter(course__code__in=class_course_codes)
                        print(f"Filtered by course codes: {class_course_codes}")
                    else:
                        print(f"No courses found for class {selected_class}")
                        
        except Class.DoesNotExist:
            print(f"Class {selected_class} not found in database")
        except Exception as e:
            print(f"Error filtering by class: {e}")
            # Fallback: show all exams
            pass
    
    if selected_date:
        exam_schedules = exam_schedules.filter(date=selected_date)
    
    # Create grid data structure
    grid_data = defaultdict(lambda: defaultdict(list))
    
    # Add exam schedules
    for exam in exam_schedules:
        # Convert date to day name
        from datetime import datetime
        exam_date = exam.date
        day_name = exam_date.strftime('%A')  # Gets day name like 'Monday'
        
        # Only show if it's a weekday
        if day_name in days:
            time_slot = exam.time_slot
            
            # Get all rooms for this exam using prefetched data
            exam_rooms = []
            try:
                # Use the prefetched room assignments
                room_assignments = exam.room_assignments.all()
                print(f"Exam {exam.course.code}: Found {room_assignments.count()} room assignments")
                
                for room_assignment in room_assignments:
                    room_info = {
                        'room_code': room_assignment.room.code,
                        'room_type': room_assignment.room.room_type.name,
                        'capacity': room_assignment.room.capacity,
                        'seating_manual': room_assignment.seating_manual
                    }
                    exam_rooms.append(room_info)
                    print(f"  - Room: {room_info['room_code']} ({room_info['room_type']})")
                
                if not exam_rooms:
                    # If no room assignments found, create a default entry
                    exam_rooms = [{'room_code': 'No Room Assigned', 'room_type': 'Unknown', 'capacity': 0, 'seating_manual': False}]
                    
            except Exception as e:
                print(f"Error getting rooms for exam {exam.course.code}: {e}")
                exam_rooms = [{'room_code': 'Error Loading', 'room_type': 'Unknown', 'capacity': 0, 'seating_manual': False}]
            
            grid_data[day_name][time_slot.id].append({
                'course_code': exam.course.code,
                'course_title': exam.course.title,
                'exam_date': exam_date.strftime('%Y-%m-%d'),
                'time_display': f"{time_slot.start_time.strftime('%H:%M')} - {time_slot.end_time.strftime('%H:%M')}",
                'duration': f"{time_slot.duration} minutes" if hasattr(time_slot, 'duration') else "Standard Duration",
                'rooms': exam_rooms
            })
    
    context = {
        'days': days,
        'time_slots': exam_time_slots,
        'grid_data': dict(grid_data),
        'user_type': 'student' if user.is_student else 'lecturer' if user.is_lecturer else 'admin',
        'all_classes': all_classes,
        'exam_dates': exam_dates,
        'selected_class': selected_class,
        'selected_date': selected_date
    }
    
    return render(request, 'portal/exam_timetable_grid.html', context)
