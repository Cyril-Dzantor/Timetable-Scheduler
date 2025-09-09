import datetime
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, HttpResponse, redirect
from .algorithm import  exam_schedule,generate_complete_schedule 
from Timetable.models import (
    Class, Room, Course, Lecturer, TimeSlot,
    ExamDate, CourseRegistration, ClassStudent
)
from Scheduler.models import ExamSchedule, LectureSchedule, StudentExamAllocation
from collections import defaultdict 
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction


def generate(request):
    try:
        # 1. Fetch basic configuration data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        time_slots = [
            f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
            for slot in TimeSlot.objects.filter(is_lecture_slot=True).order_by('start_time')
        ]
        
        # 2. Prepare courses data structure
        courses = {
            course.code: course.credit_hours 
            for course in Course.objects.all()
            if course.credit_hours > 0  # Only include valid courses
        }

        # 3. Build course-class mapping (exactly as algorithm expects)
        course_class_map = defaultdict(list)
        for course in Course.objects.prefetch_related('classes'):
            course_class_map[course.code] = [cls.code for cls in course.classes.all()]

        # 4. Build enrollment breakdown (critical for algorithm)
        enrollment_breakdown = defaultdict(lambda: defaultdict(list))
        
        # Create student->class mapping first for efficiency
        student_classes = {
            cs.student_index: cs.assigned_class.code
            for cs in ClassStudent.objects.select_related('assigned_class')
        }

        # Populate enrollment breakdown
        for reg in CourseRegistration.objects.all():
            if reg.student_index in student_classes:
                class_code = student_classes[reg.student_index]
                enrollment_breakdown[reg.course.code][class_code].append(reg.student_index)

        # 5. Prepare rooms data
        rooms = {
            room.code: room.capacity
            for room in Room.objects.filter(
                room_type__name__in=['Lecture Hall', 'Classroom','Laboratory','Auditorium'],
                capacity__gt=0  # Only include usable rooms
            )
        }

        # 6. Prepare lecturer data
        lecturers_courses_mapping = defaultdict(list)
        for course in Course.objects.prefetch_related('lecturers'):
            lecturers_courses_mapping[course.code] = [
                lecturer.name for lecturer in course.lecturers.all()
            ]

        lecturer_availability = {
            lecturer.name: lecturer.availability or {}
            for lecturer in Lecturer.objects.filter(is_active=True)
        }

        # 8. Add course_type_map
        course_type_map = {
            course.code: course.course_type.name.lower()
            for course in Course.objects.select_related('course_type')
        }

        # 9. Add course_lab_type_map (only for practicals)
        course_lab_type_map = {
            course.code: course.lab_type.name  # or .id or .code depending on what you need
            for course in Course.objects.select_related('lab_type')
            if course.lab_type  # Only include those with lab_type set
        }


        # 10. Add room_type_map
        room_type_map = {
            room.code: room.room_type.name.lower()
            for room in Room.objects.select_related('room_type')
        }

        # 11. Add lab_room_map
        lab_room_map = {}
        for room in Room.objects.select_related('lab_type'):
            if room.lab_type:
                lab_room_map[room.code] = [room.lab_type.name]  # wrap in list to match previous structure
            else:
                lab_room_map[room.code] = []



        # 7. Package data exactly as algorithm expects
        algorithm_data = {
            'courses': courses,
            'course_class_map': dict(course_class_map),
            'enrollment_breakdown': dict(enrollment_breakdown),
            'room_size': rooms,
            'lecturers_courses_mapping': dict(lecturers_courses_mapping),
            'lecturer_availability': lecturer_availability,
            'rooms': list(rooms.keys()),
            'days': days,
            'time_slots': time_slots,
            'course_type_map': course_type_map,
            'room_type_map': room_type_map,
            'lab_room_map': dict(lab_room_map),
            'course_lab_type_map': course_lab_type_map,
        }
        

        # 8. Generate schedule
        schedule, schedule_issues = generate_complete_schedule(**algorithm_data)
        print(schedule) 
        
        # 9. Store schedule in session for preview (don't save to database yet)
        if schedule:
            # Convert schedule to JSON-serializable format for session storage
            session_schedule = []
            for schedule_item in schedule:
                session_item = {
                    'course': schedule_item['course'],
                    'class': schedule_item['class'],
                    'lecturer': schedule_item['lecturer'],
                    'room': schedule_item['room'],
                    'day': schedule_item['day'],
                    'slots': schedule_item['slots'],
                    'enrollment': schedule_item.get('enrollment', 0)
                }
                session_schedule.append(session_item)
            
            # Store in session
            request.session['preview_schedule'] = session_schedule
            request.session['schedule_issues'] = schedule_issues
        
        return render(request, 'scheduler/generate.html', {
            'schedule': schedule,
            'schedule_issues': schedule_issues,
            'success': bool(schedule),
            'show_accept_button': bool(schedule),
            'debug_data': algorithm_data if not schedule else None  # For debugging
        })

    except Exception as e:
        return render(request, 'scheduler/error.html', {
            'error': f"Scheduling failed: {str(e)}",
            'success': False
        })
    
def generate_exam_schedule(request):
    try:
        # 1. Get exam-specific time data
        exam_days = [str(day.date) for day in ExamDate.objects.all().order_by('date')]
        exam_slots = [
            f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
            for slot in TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time')
        ]
        
        # 2. Prepare room data with proper dimension handling
        rooms = Room.objects.select_related('room_type').all()
        room_size = {}
        room_dimensions = {}
        max_courses = {}
        proctors_in_center = {}
        overflow_rooms = []
        
        for room in rooms:
            room_size[room.code] = room.capacity
            
            # Process dimensions - ensure proper format "rows x columns"
            if room.dimensions:
                # Clean the dimensions string
                dim_parts = room.dimensions.lower().replace(' ', '').split('x')
                if len(dim_parts) == 2 and dim_parts[0].isdigit() and dim_parts[1].isdigit():
                    room_dimensions[room.code] = f"{dim_parts[0]} x {dim_parts[1]}"
                else:
                    default_size = min(10, room.capacity)
                    room_dimensions[room.code] = f"{default_size} x {default_size}"
            else:
                default_size = min(10, room.capacity)
                
                room_dimensions[room.code] = f"{default_size} x {default_size}"
            
            max_courses[room.code] = room.max_courses
            proctors_in_center[room.code] = room.proctors_required
            
            if room.is_overflow:
                overflow_rooms.append(room.code)
        
        # 3. Prepare course data
        courses = Course.objects.select_related('course_type').all()
        student_enrollment = {course.code: course.enrollment for course in courses}
        course_type = {course.code: course.course_type.name for course in courses}
        
        # 4. Prepare enrollment breakdown - FIXED HERE
        enrollment_breakdown = defaultdict(lambda: defaultdict(list))
        
        # First create a student->class mapping
        student_class_map = {
            cs.student_index: cs.assigned_class.code
            for cs in ClassStudent.objects.all()
        }
        
        # Then populate enrollment breakdown
        for reg in CourseRegistration.objects.select_related('course').all():
            if reg.student_index in student_class_map:
                class_code = student_class_map[reg.student_index]
                enrollment_breakdown[reg.course.code][class_code].append(reg.student_index)
        
        # 5. Prepare proctor data
        proctors = Lecturer.objects.filter(is_proctor=True)
        proctors_list = [proctor.name for proctor in proctors]
        proctors_availability = {}
        
        for proctor in proctors:
            try:
                availability = json.loads(proctor.proctor_availability) if proctor.proctor_availability else {}
                proctors_availability[proctor.name] = availability
            except json.JSONDecodeError:
                proctors_availability[proctor.name] = {}
        
        # 6. Package all data for the algorithm
        exam_data = {
            'student_enrollment': student_enrollment,
            'course_type': course_type,
            'exam_days': exam_days,
            'exam_slots': exam_slots,
            'room_size': room_size,
            'room_dimensions': room_dimensions,
            'overflow_rooms': overflow_rooms,
            'max_courses': max_courses,
            'proctors_in_center': proctors_in_center,
            'proctors': proctors_list,
            'proctors_availability': proctors_availability,
            'enrollment_breakdown': dict(enrollment_breakdown),
        }
        
        # 7. Run the exam scheduling algorithm
        schedule, manual_assignments, unused_columns = exam_schedule(**exam_data)
        
        # 8. Store exam schedule in session for preview (don't save to database yet)
        if schedule:
            # Store the original schedule data in session (convert sets to lists for JSON serialization)
            import copy
            session_exam_schedule = copy.deepcopy(schedule)
            
            # Convert any sets to lists for JSON serialization
            for exam in session_exam_schedule:
                for room in exam['rooms']:
                    if 'student_ids' in room and isinstance(room['student_ids'], set):
                        room['student_ids'] = list(room['student_ids'])
                    if 'columns_used' in room and isinstance(room['columns_used'], set):
                        room['columns_used'] = list(room['columns_used'])
                
                # Convert proctors sets to lists
                for room_code, proctors in exam['proctors'].items():
                    if isinstance(proctors, set):
                        exam['proctors'][room_code] = list(proctors)
            
            # Store in session
            request.session['preview_exam_schedule'] = session_exam_schedule
            request.session['exam_manual_assignments'] = manual_assignments
            request.session['exam_unused_columns'] = unused_columns
        
        # 9. Process the results for the template
        processed_schedule = []
        for exam in schedule:
            rooms_info = []
            for room in exam['rooms']:
                rooms_info.append({
                    'room': room['room'],
                    'class': room['class'],
                    'students_count': len(room['student_ids']),
                    'columns_used': (', '.join(map(str, room['columns_used']))) 
                                   if isinstance(room['columns_used'], (set, list))
                                   else room['columns_used']
                })
            
            processed_schedule.append({
                'course': exam['course'],
                'day': exam['day'],
                'slot': exam['slot'],
                'rooms': rooms_info,
                'proctors': {room: list(proctors) for room, proctors in exam['proctors'].items()}
            })
        
        # 10. Prepare context for template
        context = {
            'exam_schedule': processed_schedule,
            'manual_assignments': manual_assignments,
            'unused_columns': unused_columns,
            'exam_days': exam_days,
            'exam_slots': exam_slots,
            'success': True,
            'show_accept_button': bool(schedule)
        }


     
        
        return render(request, 'scheduler/exam_schedule.html', context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render(request, 'scheduler/error.html', {
            'error': f"Exam scheduling failed: {str(e)}",
            'success': False
        })

def generate_schedule(request):
    return render(request, 'scheduler/generate_schedule.html')

def edit_schedule(request):
    return render(request, 'scheduler/edit_schedule.html')

def accept_schedule(request):
    """Accept and save the previewed schedule to database"""
    if 'preview_schedule' not in request.session:
        messages.warning(request, "No schedule to accept. Please generate a schedule first.")
        return redirect('scheduler:generate')
    
    schedule_to_save = request.session['preview_schedule']
    schedule_issues = request.session.get('schedule_issues', [])

    if not schedule_to_save:
        messages.warning(request, "No schedule to accept. Please generate a schedule first.")
        return redirect('scheduler:generate')

    try:
        # Clear existing schedules first
        LectureSchedule.objects.all().delete()
        
        # Save new schedules
        saved_count = 0
        for schedule_item in schedule_to_save:
            try:
                # Get the course
                course = Course.objects.get(code=schedule_item['course'])
                
                # Get the class
                assigned_class = Class.objects.get(code=schedule_item['class'])
                
                # Get the lecturer (first one if multiple)
                lecturer_name = schedule_item['lecturer']
                lecturer = Lecturer.objects.filter(name=lecturer_name).first()
                
                # Get the room
                room = Room.objects.get(code=schedule_item['room'])
                
                # Process each time slot individually
                for slot in schedule_item['slots']:
                    # Clean up the slot string (remove any extra spaces)
                    slot = slot.strip()
                    
                    # Split the slot into start and end times
                    if ' - ' in slot:
                        start_time_str, end_time_str = slot.split(' - ')
                    else:
                        print(f"Invalid slot format: {slot}")
                        continue
                    
                    # Convert to time objects
                    from datetime import datetime
                    try:
                        start_time = datetime.strptime(start_time_str, '%H:%M').time()
                        end_time = datetime.strptime(end_time_str, '%H:%M').time()
                    except ValueError:
                        print(f"Invalid time format in slot: {slot}")
                        continue
                    
                    # Create or get the time slot
                    time_slot, created = TimeSlot.objects.get_or_create(
                        start_time=start_time,
                        end_time=end_time,
                        defaults={'code': f"{start_time_str}-{end_time_str}", 'is_lecture_slot': True}
                    )
                    
                    # Create LectureSchedule object for this time slot
                    LectureSchedule.objects.create(
                        course=course,
                        assigned_class=assigned_class,
                        lecturer=lecturer,
                        room=room,
                        day=schedule_item['day'],
                        time_slot=time_slot,
                        enrollment=schedule_item.get('enrollment', 0)
                    )
                    saved_count += 1
                    print(f"Saved: {course.code} - {assigned_class.code} - {schedule_item['day']} - {slot}")
                
            except Exception as e:
                print(f"Error saving schedule item: {e}")
                continue

        messages.success(request, f"Schedule accepted and saved successfully! {saved_count} sessions saved to database.")
        
        # Clear session data
        del request.session['preview_schedule']
        del request.session['schedule_issues']
        
        return redirect('scheduler:generate')
        
    except Exception as e:
        messages.error(request, f"Error saving schedule: {str(e)}")
        return redirect('scheduler:generate')

def accept_exam_schedule(request):
    """Accept and save the previewed exam schedule to database"""
    if 'preview_exam_schedule' not in request.session:
        messages.warning(request, "No exam schedule to accept. Please generate an exam schedule first.")
        return redirect('scheduler:generate_exam_schedule')
    
    exam_schedule_to_save = request.session['preview_exam_schedule']
    manual_assignments = request.session.get('exam_manual_assignments', [])
    unused_columns = request.session.get('exam_unused_columns', [])

    if not exam_schedule_to_save:
        messages.warning(request, "No exam schedule to accept. Please generate an exam schedule first.")
        return redirect('scheduler:generate_exam_schedule')

    try:
        # Clear existing exam schedules first
        from Scheduler.models import ExamSchedule, ExamRoomAssignment, ExamRoomClassAllocation, StudentExamAllocation
        ExamSchedule.objects.all().delete()
        ExamRoomAssignment.objects.all().delete()
        ExamRoomClassAllocation.objects.all().delete()
        StudentExamAllocation.objects.all().delete()
        
        # Save new exam schedules
        saved_count = 0
        for exam_item in exam_schedule_to_save:
            try:
                # Get the course
                course = Course.objects.get(code=exam_item['course'])
                
                # Parse the exam date
                from datetime import datetime
                exam_date = datetime.strptime(exam_item['day'], '%Y-%m-%d').date()
                
                # Get or create time slot
                start_time_str, end_time_str = exam_item['slot'].split(' - ')
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                time_slot, created = TimeSlot.objects.get_or_create(
                    start_time=start_time,
                    end_time=end_time,
                    defaults={'code': f"{start_time_str}-{end_time_str}", 'is_exam_slot': True}
                )
                
                # Create ExamSchedule object
                exam_schedule = ExamSchedule.objects.create(
                    course=course,
                    date=exam_date,
                    time_slot=time_slot
                )
                
                # Create room assignments and allocations
                print(f"\nProcessing exam: {exam_item['course']} on {exam_item['day']} at {exam_item['slot']}")
                print(f"Number of rooms: {len(exam_item['rooms'])}")
                
                for room_data in exam_item['rooms']:
                    print(f"Processing room: {room_data['room']} for class: {room_data['class']}")
                    room = Room.objects.get(code=room_data['room'])
                    
                    # Create ExamRoomAssignment
                    room_assignment = ExamRoomAssignment.objects.create(
                        exam=exam_schedule,
                        room=room
                    )
                    
                    # Add proctors if available
                    if room_data['room'] in exam_item['proctors']:
                        proctor_names = exam_item['proctors'][room_data['room']]
                        for proctor_name in proctor_names:
                            proctor = Lecturer.objects.filter(name=proctor_name).first()
                            if proctor:
                                room_assignment.proctors.add(proctor)
                    
                    # Create class allocation
                    try:
                        print(f"Looking for class with code: {room_data['class']}")
                        print(f"Room data keys: {list(room_data.keys())}")
                        print(f"Room data: {room_data}")
                        
                        class_obj = Class.objects.get(code=room_data['class'])
                        print(f"Found class: {class_obj.code} - {class_obj.name}")
                        
                        # Get student count from the correct key
                        student_count = room_data.get('students_count', room_data.get('student_count', len(room_data.get('student_ids', []))))
                        print(f"Student count: {student_count}")
                        
                        ExamRoomClassAllocation.objects.create(
                            room_assignment=room_assignment,
                            class_assigned=class_obj,
                            columns_used=room_data.get('columns_used', []),
                            student_count=student_count
                        )
                        print(f"Created ExamRoomClassAllocation for {class_obj.code}")
                    except Class.DoesNotExist:
                        print(f"ERROR: Class with code '{room_data['class']}' not found in database")
                        # List available classes for debugging
                        available_classes = list(Class.objects.values_list('code', flat=True))
                        print(f"Available classes: {available_classes}")
                    except Exception as e:
                        print(f"ERROR creating ExamRoomClassAllocation: {e}")
                        print(f"Full room_data: {room_data}")
                    
                    # Create student allocations
                    for student_id in room_data['student_ids']:
                        StudentExamAllocation.objects.create(
                            student_index=student_id,
                            exam=exam_schedule,
                            room=room,
                            column_number=room_data.get('column_number', 0)
                        )
                
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving exam schedule item: {e}")
                continue

        messages.success(request, f"Exam schedule accepted and saved successfully! {saved_count} exams saved to database.")
        
        # Clear session data
        del request.session['preview_exam_schedule']
        del request.session['exam_manual_assignments']
        del request.session['exam_unused_columns']
        
        return redirect('scheduler:generate_exam_schedule')
        
    except Exception as e:
        messages.error(request, f"Error saving exam schedule: {str(e)}")
        return redirect('scheduler:generate_exam_schedule')
    

@login_required
def edit_exam_schedule(request, exam_id):
    """
    Edit a specific exam schedule entry - Admin only
    Enhanced with comprehensive conflict checking and guidance
    """
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "Only administrators can edit exam schedules.")
        return redirect('portal:exam_timetable_grid')
    
    exam_schedule = get_object_or_404(ExamSchedule, id=exam_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            course_id = request.POST.get('course')
            exam_date = request.POST.get('exam_date')
            time_slot_id = request.POST.get('time_slot')
            
            # Validate required fields
            if not all([course_id, exam_date, time_slot_id]):
                messages.error(request, "All fields are required.")
                return redirect('scheduler:edit_exam_schedule', exam_id=exam_id)
            
            # Get related objects
            course = Course.objects.get(id=course_id)
            time_slot = TimeSlot.objects.get(id=time_slot_id)
            
            # Parse the date
            exam_date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            
            # Check for conflicts before updating
            conflicts = ExamSchedule.objects.filter(
                date=exam_date_obj,
                time_slot=time_slot
            ).exclude(id=exam_id)
            
            # Detailed conflict checking with specific information
            conflict_details = []
            
            # Check course conflicts (same course at different time)
            course_conflicts = conflicts.filter(course=course)
            if course_conflicts.exists():
                for conflict in course_conflicts:
                    conflict_details.append({
                        'type': 'course',
                        'message': f"Course {course.code} is already scheduled",
                        'details': f"Date: {conflict.date} | Time: {conflict.time_slot}",
                        'conflict_schedule': conflict
                    })
            
            # Check room conflicts (same room at same time)
            room_conflicts = []
            for conflict in conflicts:
                # Get all rooms used by this conflicting exam
                conflict_rooms = conflict.room_assignments.all()
                for conflict_room in conflict_rooms:
                    room_conflicts.append({
                        'type': 'room',
                        'message': f"Room {conflict_room.room.code} is already booked",
                        'details': f"Course: {conflict.course.code} | Date: {conflict.date} | Time: {conflict.time_slot}",
                        'conflict_schedule': conflict,
                        'conflict_room': conflict_room.room
                    })
            
            # Check proctor conflicts (same proctor at same time)
            proctor_conflicts = []
            for conflict in conflicts:
                conflict_rooms = conflict.room_assignments.all()
                for conflict_room in conflict_rooms:
                    for proctor in conflict_room.proctors.all():
                        proctor_conflicts.append({
                            'type': 'proctor',
                            'message': f"Proctor {proctor.name} is already assigned",
                            'details': f"Course: {conflict.course.code} | Room: {conflict_room.room.code} | Date: {conflict.date} | Time: {conflict.time_slot}",
                            'conflict_schedule': conflict,
                            'conflict_proctor': proctor
                        })
            
            # Add all conflicts to the list
            conflict_details.extend(room_conflicts)
            conflict_details.extend(proctor_conflicts)
            
            # If there are conflicts, show detailed information
            if conflict_details:
                context = {
                    'exam_schedule': exam_schedule,
                    'courses': Course.objects.all().order_by('code'),
                    'time_slots': TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time'),
                    'conflict_details': conflict_details,
                    'form_data': {
                        'course_id': course_id,
                        'exam_date': exam_date,
                        'time_slot_id': time_slot_id
                    }
                }
                return render(request, 'scheduler/edit_exam_schedule.html', context)
            
            # Update the exam schedule if no conflicts
            exam_schedule.course = course
            exam_schedule.date = exam_date_obj
            exam_schedule.time_slot = time_slot
            exam_schedule.save()
            
            messages.success(request, f"Exam schedule updated successfully! {course.code} - {exam_date_obj} {time_slot}")
            return redirect('portal:exam_timetable_grid')
            
        except (Course.DoesNotExist, TimeSlot.DoesNotExist) as e:
            messages.error(request, f"Invalid selection: {str(e)}")
            return redirect('scheduler:edit_exam_schedule', exam_id=exam_id)
        except Exception as e:
            messages.error(request, f"Error updating exam schedule: {str(e)}")
            return redirect('scheduler:edit_exam_schedule', exam_id=exam_id)
    
    
    
    # Get current exam details
    current_course = exam_schedule.course
    current_date = exam_schedule.date
    current_time_slot = exam_schedule.time_slot
    
    # Get all available courses with enrollment info
    courses_with_enrollment = Course.objects.annotate(
        student_count=Count('students', distinct=True)
    ).order_by('code')
    
    # Get all exam time slots
    exam_time_slots = TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time')
    
    # Get official exam dates only
    exam_dates = list(ExamDate.objects.all().order_by('date'))
    future_dates = [exam_date.date for exam_date in exam_dates]
    
    # Get first and last exam dates for display
    first_exam_date = exam_dates[0] if exam_dates else None
    last_exam_date = exam_dates[-1] if exam_dates else None
    
    # Get availability analysis for current exam
    availability_analysis = get_exam_availability_analysis(
        current_course, current_date, current_time_slot, exam_schedule
    )
    
    # Get room availability for the current time slot
    room_availability = get_room_availability_analysis(current_date, current_time_slot)
    
    # Get proctor availability for the current time slot
    proctor_availability = get_proctor_availability_analysis(current_date, current_time_slot)
    
    # Get alternative suggestions
    alternative_suggestions = get_alternative_exam_slots(current_course, current_date, current_time_slot)
    
    context = {
        'exam_schedule': exam_schedule,
        'courses': courses_with_enrollment,
        'time_slots': exam_time_slots,
        'exam_dates': exam_dates,
        'first_exam_date': first_exam_date,
        'last_exam_date': last_exam_date,
        'availability_analysis': availability_analysis,
        'room_availability': room_availability,
        'proctor_availability': proctor_availability,
        'alternative_suggestions': alternative_suggestions,
    }
    
    return render(request, 'scheduler/edit_exam_schedule.html', context)


def get_exam_availability_analysis(course, date, time_slot, current_exam):
    """Analyze availability for a specific exam slot"""
    
    # Get conflicting exams (excluding current exam)
    conflicting_exams = ExamSchedule.objects.filter(
        date=date,
        time_slot=time_slot
    ).exclude(id=current_exam.id)
    
    # Get course enrollment
    student_count = course.students.count()
    
    # Get available rooms for this time slot
    available_rooms = Room.objects.filter(
        ~Q(examroomassignment__exam__date=date, examroomassignment__exam__time_slot=time_slot)
    ).order_by('-capacity')
    
    # Get available proctors
    available_proctors = Lecturer.objects.filter(
        is_proctor=True
    ).exclude(
        examroomassignment__exam__date=date, 
        examroomassignment__exam__time_slot=time_slot
    )
    
    return {
        'conflicting_exams': conflicting_exams,
        'student_count': student_count,
        'available_rooms': available_rooms,
        'available_proctors': available_proctors,
        'total_room_capacity': sum(room.capacity for room in available_rooms),
        'total_proctors': available_proctors.count(),
    }


def get_room_availability_analysis(date, time_slot):
    """Analyze room availability for a specific time slot"""
    
    # Get all rooms
    all_rooms = Room.objects.all().order_by('-capacity')
    
    # Get booked rooms for this time slot
    booked_rooms = Room.objects.filter(
        examroomassignment__exam__date=date,
        examroomassignment__exam__time_slot=time_slot
    )
    
    # Get available rooms
    available_rooms = all_rooms.exclude(id__in=booked_rooms.values_list('id', flat=True))
    
    # Categorize rooms by type
    room_categories = {}
    for room in all_rooms:
        room_type = getattr(room.room_type, 'name', 'Unknown')
        if room_type not in room_categories:
            room_categories[room_type] = {'total': 0, 'available': 0, 'booked': 0}
        
        room_categories[room_type]['total'] += 1
        if room in available_rooms:
            room_categories[room_type]['available'] += 1
        else:
            room_categories[room_type]['booked'] += 1
    
    return {
        'all_rooms': all_rooms,
        'booked_rooms': booked_rooms,
        'available_rooms': available_rooms,
        'room_categories': room_categories,
        'total_capacity': sum(room.capacity for room in available_rooms),
    }


def get_proctor_availability_analysis(date, time_slot):
    """Analyze proctor availability for a specific time slot"""
    
    # Get all proctors
    all_proctors = Lecturer.objects.filter(is_proctor=True)
    
    # Get booked proctors for this time slot
    booked_proctors = Lecturer.objects.filter(
        is_proctor=True,
        examroomassignment__exam__date=date,
        examroomassignment__exam__time_slot=time_slot
    )
    
    # Get available proctors
    available_proctors = all_proctors.exclude(id__in=booked_proctors.values_list('id', flat=True))
    
    return {
        'all_proctors': all_proctors,
        'booked_proctors': booked_proctors,
        'available_proctors': available_proctors,
        'total_proctors': all_proctors.count(),
        'available_count': available_proctors.count(),
    }


def get_alternative_exam_slots(course, current_date, current_time_slot):
    """Get alternative time slots for the course within exam period only"""
    
    # Get all exam dates (excluding current date)
    exam_dates = ExamDate.objects.exclude(date=current_date).order_by('date')
    alternative_dates = [exam_date.date for exam_date in exam_dates]
    
    # Get all exam time slots
    all_time_slots = TimeSlot.objects.filter(is_exam_slot=True).order_by('start_time')
    
    alternatives = []
    for alt_date in alternative_dates:
        for alt_time_slot in all_time_slots:
            # Check if this slot is available for the course
            conflicting_exams = ExamSchedule.objects.filter(
                date=alt_date,
                time_slot=alt_time_slot,
                course=course
            )
            
            if not conflicting_exams.exists():
                # Check room availability
                available_rooms = Room.objects.filter(
                    ~Q(examroomassignment__exam__date=alt_date, examroomassignment__exam__time_slot=alt_time_slot)
                )
                
                # Check proctor availability
                available_proctors = Lecturer.objects.filter(
                    is_proctor=True
                ).exclude(
                    examroomassignment__exam__date=alt_date, 
                    examroomassignment__exam__time_slot=alt_time_slot
                )
                
                alternatives.append({
                    'date': alt_date,
                    'time_slot': alt_time_slot,
                    'available_rooms': available_rooms.count(),
                    'available_proctors': available_proctors.count(),
                    'total_capacity': sum(room.capacity for room in available_rooms),
                })
    
    # Sort by date and time
    alternatives.sort(key=lambda x: (x['date'], x['time_slot'].start_time))
    
    return alternatives[:10]  # Return top 10 alternatives


@login_required
def delete_exam_schedule(request, exam_id):
    """
    Delete a specific exam schedule entry - Admin only
    """
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "Only administrators can delete exam schedules.")
        return redirect('portal:exam_timetable_grid')
    
    exam_schedule = get_object_or_404(ExamSchedule, id=exam_id)
    
    if request.method == 'POST':
        course_info = f"{exam_schedule.course.code} - {exam_schedule.date} {exam_schedule.time_slot}"
        exam_schedule.delete()
        messages.success(request, f"Exam schedule deleted: {course_info}")
        return redirect('portal:exam_timetable_grid')
    
    context = {
        'exam_schedule': exam_schedule
    }
    
    return render(request, 'scheduler/delete_exam_schedule.html', context)


@login_required
def edit_schedule(request, schedule_id):
    """
    Edit a specific schedule entry - Admin only
    """
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "Only administrators can edit schedules.")
        return redirect('portal:timetable_grid')
    
    schedule = get_object_or_404(LectureSchedule, id=schedule_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            course_id = request.POST.get('course')
            lecturer_id = request.POST.get('lecturer')
            room_id = request.POST.get('room')
            day = request.POST.get('day')
            time_slot_id = request.POST.get('time_slot')
            assigned_class_id = request.POST.get('assigned_class')
            
            # Validate required fields
            if not all([course_id, lecturer_id, room_id, day, time_slot_id, assigned_class_id]):
                messages.error(request, "All fields are required.")
                return redirect('scheduler:edit_schedule', schedule_id=schedule_id)
            
            # Get related objects
            course = Course.objects.get(id=course_id)
            lecturer = Lecturer.objects.get(id=lecturer_id)
            room = Room.objects.get(id=room_id)
            time_slot = TimeSlot.objects.get(id=time_slot_id)
            assigned_class = Class.objects.get(id=assigned_class_id)
            
            # Check for conflicts before updating
            conflicts = LectureSchedule.objects.filter(
                day=day,
                time_slot=time_slot
            ).exclude(id=schedule_id)
            
            # Detailed conflict checking with specific information
            conflict_details = []
            
            # Check room conflicts
            room_conflicts = conflicts.filter(room=room)
            if room_conflicts.exists():
                for conflict in room_conflicts:
                    conflict_details.append({
                        'type': 'room',
                        'message': f"Room {room.code} is already booked",
                        'details': f"Course: {conflict.course.code} | Lecturer: {conflict.lecturer.name} | Class: {conflict.assigned_class.code}",
                        'conflict_schedule': conflict
                    })
            
            # Check lecturer conflicts
            lecturer_conflicts = conflicts.filter(lecturer=lecturer)
            if lecturer_conflicts.exists():
                for conflict in lecturer_conflicts:
                    conflict_details.append({
                        'type': 'lecturer',
                        'message': f"Lecturer {lecturer.name} is already assigned",
                        'details': f"Course: {conflict.course.code} | Room: {conflict.room.code} | Class: {conflict.assigned_class.code}",
                        'conflict_schedule': conflict
                    })
            
            # Check class conflicts
            class_conflicts = conflicts.filter(assigned_class=assigned_class)
            if class_conflicts.exists():
                for conflict in class_conflicts:
                    conflict_details.append({
                        'type': 'class',
                        'message': f"Class {assigned_class.code} is already scheduled",
                        'details': f"Course: {conflict.course.code} | Lecturer: {conflict.lecturer.name} | Room: {conflict.room.code}",
                        'conflict_schedule': conflict
                    })
            
            # If there are conflicts, show detailed information
            if conflict_details:
                context = {
                    'schedule': schedule,
                    'courses': Course.objects.all().order_by('code'),
                    'lecturers': Lecturer.objects.filter(is_active=True).order_by('name'),
                    'rooms': Room.objects.all().order_by('code'),
                    'time_slots': TimeSlot.objects.filter(is_lecture_slot=True).order_by('start_time'),
                    'classes': Class.objects.all().order_by('code'),
                    'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                    'conflict_details': conflict_details,
                    'form_data': {
                        'course_id': course_id,
                        'lecturer_id': lecturer_id,
                        'room_id': room_id,
                        'day': day,
                        'time_slot_id': time_slot_id,
                        'assigned_class_id': assigned_class_id
                    }
                }
                return render(request, 'scheduler/edit_schedule.html', context)
            
            # Update the schedule if no conflicts
            schedule.course = course
            schedule.lecturer = lecturer
            schedule.room = room
            schedule.day = day
            schedule.time_slot = time_slot
            schedule.assigned_class = assigned_class
            schedule.save()
            
            messages.success(request, f"Schedule updated successfully! {course.code} - {day} {time_slot}")
            return redirect('portal:timetable_grid')
            
        except (Course.DoesNotExist, Lecturer.DoesNotExist, Room.DoesNotExist, 
                TimeSlot.DoesNotExist, Class.DoesNotExist) as e:
            messages.error(request, f"Invalid selection: {str(e)}")
            return redirect('scheduler:edit_schedule', schedule_id=schedule_id)
        except Exception as e:
            messages.error(request, f"Error updating schedule: {str(e)}")
            return redirect('scheduler:edit_schedule', schedule_id=schedule_id)
    
    # GET request - show edit form
    context = {
        'schedule': schedule,
        'courses': Course.objects.all().order_by('code'),
        'lecturers': Lecturer.objects.filter(is_active=True).order_by('name'),
        'rooms': Room.objects.all().order_by('code'),
        'time_slots': TimeSlot.objects.filter(is_lecture_slot=True).order_by('start_time'),
        'classes': Class.objects.all().order_by('code'),
        'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    }
    
    return render(request, 'scheduler/edit_schedule.html', context)

@login_required
def delete_schedule(request, schedule_id):
    """
    Delete a specific schedule entry - Admin only
    """
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "Only administrators can delete schedules.")
        return redirect('portal:timetable_grid')
    
    schedule = get_object_or_404(LectureSchedule, id=schedule_id)
    
    if request.method == 'POST':
        course_info = f"{schedule.course.code} - {schedule.day} {schedule.time_slot}"
        schedule.delete()
        messages.success(request, f"Schedule deleted: {course_info}")
        return redirect('portal:timetable_grid')
    
    context = {
        'schedule': schedule
    }
    
    return render(request, 'scheduler/delete_schedule.html', context)

@login_required
def add_schedule(request):
    """
    Add a new schedule entry manually - Admin only
    """
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "Only administrators can add schedules.")
        return redirect('portal:timetable_grid')
    
    if request.method == 'POST':
        try:
            # Get form data
            course_id = request.POST.get('course')
            lecturer_id = request.POST.get('lecturer')
            room_id = request.POST.get('room')
            day = request.POST.get('day')
            time_slot_id = request.POST.get('time_slot')
            assigned_class_id = request.POST.get('assigned_class')
            
            # Validate required fields
            if not all([course_id, lecturer_id, room_id, day, time_slot_id, assigned_class_id]):
                messages.error(request, "All fields are required.")
                return redirect('scheduler:add_schedule')
            
            # Get related objects
            course = Course.objects.get(id=course_id)
            lecturer = Lecturer.objects.get(id=lecturer_id)
            room = Room.objects.get(id=room_id)
            time_slot = TimeSlot.objects.get(id=time_slot_id)
            assigned_class = Class.objects.get(id=assigned_class_id)
            
            # Check for conflicts
            conflicts = LectureSchedule.objects.filter(
                day=day,
                time_slot=time_slot
            )
            
            # Detailed conflict checking with specific information
            conflict_details = []
            
            # Check room conflicts
            room_conflicts = conflicts.filter(room=room)
            if room_conflicts.exists():
                for conflict in room_conflicts:
                    conflict_details.append({
                        'type': 'room',
                        'message': f"Room {room.code} is already booked",
                        'details': f"Course: {conflict.course.code} | Lecturer: {conflict.lecturer.name} | Class: {conflict.assigned_class.code}",
                        'conflict_schedule': conflict
                    })
            
            # Check lecturer conflicts
            lecturer_conflicts = conflicts.filter(lecturer=lecturer)
            if lecturer_conflicts.exists():
                for conflict in lecturer_conflicts:
                    conflict_details.append({
                        'type': 'lecturer',
                        'message': f"Lecturer {lecturer.name} is already assigned",
                        'details': f"Course: {conflict.course.code} | Room: {conflict.room.code} | Class: {conflict.assigned_class.code}",
                        'conflict_schedule': conflict
                    })
            
            # Check class conflicts
            class_conflicts = conflicts.filter(assigned_class=assigned_class)
            if class_conflicts.exists():
                for conflict in class_conflicts:
                    conflict_details.append({
                        'type': 'class',
                        'message': f"Class {assigned_class.code} is already scheduled",
                        'details': f"Course: {conflict.course.code} | Lecturer: {conflict.lecturer.name} | Room: {conflict.room.code}",
                        'conflict_schedule': conflict
                    })
            
            # If there are conflicts, show detailed information
            if conflict_details:
                context = {
                    'courses': Course.objects.all().order_by('code'),
                    'lecturers': Lecturer.objects.filter(is_active=True).order_by('name'),
                    'rooms': Room.objects.all().order_by('code'),
                    'time_slots': TimeSlot.objects.filter(is_lecture_slot=True).order_by('start_time'),
                    'classes': Class.objects.all().order_by('code'),
                    'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                    'conflict_details': conflict_details,
                    'form_data': {
                        'course_id': course_id,
                        'lecturer_id': lecturer_id,
                        'room_id': room_id,
                        'day': day,
                        'time_slot_id': time_slot_id,
                        'assigned_class_id': assigned_class_id
                    }
                }
                return render(request, 'scheduler/add_schedule.html', context)
            
            # Create new schedule
            new_schedule = LectureSchedule.objects.create(
                course=course,
                lecturer=lecturer,
                room=room,
                day=day,
                time_slot=time_slot,
                assigned_class=assigned_class
            )
            
            messages.success(request, f"Schedule added successfully! {course.code} - {day} {time_slot}")
            return redirect('portal:timetable_grid')
            
        except (Course.DoesNotExist, Lecturer.DoesNotExist, Room.DoesNotExist, 
                TimeSlot.DoesNotExist, Class.DoesNotExist) as e:
            messages.error(request, f"Invalid selection: {str(e)}")
            return redirect('scheduler:add_schedule')
        except Exception as e:
            messages.error(request, f"Error creating schedule: {str(e)}")
            return redirect('scheduler:add_schedule')
    
    # GET request - show add form
    context = {
        'courses': Course.objects.all().order_by('code'),
        'lecturers': Lecturer.objects.filter(is_active=True).order_by('name'),
        'rooms': Room.objects.all().order_by('code'),
        'time_slots': TimeSlot.objects.filter(is_lecture_slot=True).order_by('start_time'),
        'classes': Class.objects.all().order_by('code'),
        'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    }
    
    return render(request, 'scheduler/add_schedule.html', context)
