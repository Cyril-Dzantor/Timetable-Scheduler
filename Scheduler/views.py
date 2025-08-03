from django.shortcuts import render, HttpResponse, redirect
from .algorithm import  exam_schedule,generate_complete_schedule 
from Timetable.models import (
    Class, Room, Course, Lecturer, TimeSlot,
    ExamDate, CourseRegistration, ClassStudent
)
from Scheduler.models import LectureSchedule
from collections import defaultdict 
import json
from django.contrib import messages

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

def accept_schedule(request):
    """Accept and save the previewed schedule to database"""
    if 'preview_schedule' not in request.session:
        messages.warning(request, "No schedule to accept. Please generate a schedule first.")
        return redirect('generate')
    
    schedule_to_save = request.session['preview_schedule']
    schedule_issues = request.session.get('schedule_issues', [])

    if not schedule_to_save:
        messages.warning(request, "No schedule to accept. Please generate a schedule first.")
        return redirect('generate')

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
                
                # Get or create time slot
                start_time_str, end_time_str = schedule_item['slots'][0].split(' - ')
                from datetime import datetime
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                time_slot, created = TimeSlot.objects.get_or_create(
                    start_time=start_time,
                    end_time=end_time,
                    defaults={'code': f"{start_time_str}-{end_time_str}", 'is_lecture_slot': True}
                )
                
                # Create LectureSchedule object
                LectureSchedule.objects.create(
                    course=course,
                    assigned_class=assigned_class,
                    lecturer=lecturer,
                    room=room,
                    day=schedule_item['day'],
                    time_slot=time_slot
                )
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving schedule item: {e}")
                continue

        messages.success(request, f"Schedule accepted and saved successfully! {saved_count} sessions saved to database.")
        
        # Clear session data
        del request.session['preview_schedule']
        del request.session['schedule_issues']
        
        return redirect('generate')
        
    except Exception as e:
        messages.error(request, f"Error saving schedule: {str(e)}")
        return redirect('generate')

def accept_exam_schedule(request):
    """Accept and save the previewed exam schedule to database"""
    if 'preview_exam_schedule' not in request.session:
        messages.warning(request, "No exam schedule to accept. Please generate an exam schedule first.")
        return redirect('generate_exam_schedule')
    
    exam_schedule_to_save = request.session['preview_exam_schedule']
    manual_assignments = request.session.get('exam_manual_assignments', [])
    unused_columns = request.session.get('exam_unused_columns', [])

    if not exam_schedule_to_save:
        messages.warning(request, "No exam schedule to accept. Please generate an exam schedule first.")
        return redirect('generate_exam_schedule')

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
        
        return redirect('generate_exam_schedule')
        
    except Exception as e:
        messages.error(request, f"Error saving exam schedule: {str(e)}")
        return redirect('generate_exam_schedule')

