from django.shortcuts import render, HttpResponse
from .algorithm import  exam_schedule,generate_complete_schedule 
from Timetable.models import (
    Class, Room, Course, Lecturer, TimeSlot,
    ExamDate, CourseRegistration, ClassStudent
)
from collections import defaultdict 
import json 

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
        
        return render(request, 'scheduler/generate.html', {
            'schedule': schedule,
            'success': bool(schedule),
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
        
        # 8. Process the results for the template
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
        
        # 9. Prepare context for template
        context = {
            'exam_schedule': processed_schedule,
            'manual_assignments': manual_assignments,
            'unused_columns': unused_columns,
            'exam_days': exam_days,
            'exam_slots': exam_slots,
            'success': True
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

# def generate(request):
#     # Classes
#     classes = list(Class.objects.values_list('class_code', flat=True))
#     class_size = {c.class_code: c.class_size for c in Class.objects.all()}

#     # Rooms
#     rooms = list(Room.objects.values_list('room_code', flat=True))
#     room_size = {r.room_code: r.capacity for r in Room.objects.all()}

#     # Days and Time Slots
#     days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
#     lecture_hours = [
#         '8:00 - 8:55', '9:00 - 9:55', '10:30 - 11:25', '11:30 - 12:25',
#         '13:00 - 13:55', '14:00 - 14:55', '15:00 - 15:55',
#         '16:00 - 16:55', '17:00 - 17:55', '18:00 - 18:55'
#     ]

#     # Courses and related data
#     courses = list(Course.objects.values_list('course_code', flat=True))
#     course_credit_hours = {c.course_code: c.credit_hours for c in Course.objects.all()}
#     student_enrollment = {c.course_code: c.students_enrolled for c in Course.objects.all()}
    
#     # Prerequisites
#     course_prerequisites = {
#         c.course_code: [p.course_code for p in c.course_prerequisites.all()]
#         for c in Course.objects.all()
#     }

#     # Lecturers and availability
#     lecturers = list(Lecturer.objects.values_list('name', flat=True))
#     lecturer_availability = {
#         l.name: l.availability for l in Lecturer.objects.all()
#     }

#     # Lecturer-course mapping (Many-to-Many)
#     lecturers_courses_mapping = {
#         l.name: [c.course_code for c in l.courses.all()]
#         for l in Lecturer.objects.all()
#     }

#     # You can now pass this data to your algorithm
#     best_schedule = run_genetic_algorithm(
#         class_size=class_size,
#         rooms=rooms,
#         room_size=room_size,
#         days=days,
#         lecture_hours=lecture_hours,
#         courses=courses,
#         course_credit_hours=course_credit_hours,
#         student_enrollment=student_enrollment,
#         course_prerequisites=course_prerequisites,
#         lecturers=lecturers,
#         lecturers_courses_mapping=lecturers_courses_mapping,
#         lecturer_availability=lecturer_availability,
#     )

#     return render(request, 'scheduler/generate.html', best_schedule)