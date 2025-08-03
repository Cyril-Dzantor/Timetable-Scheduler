from django.shortcuts import render,HttpResponse,redirect
from django.shortcuts import get_object_or_404
from .models import Room,Class,Lecturer,Course,Building, RoomType, LabType,Department,CourseType,ClassStudent,CourseRegistration,Broadcast
from Users.models import LecturerProfile
from .forms import BroadcastForm
from django.contrib.auth.decorators import login_required
from Scheduler.models import LectureSchedule
from django.db.models import Q

from django.http import FileResponse, Http404
from django.conf import settings
import os 


from Users.models import StudentProfile


# Create your views here.
def timetable(request):
    return HttpResponse('Test')

def rooms(request):
    rooms = Room.objects.all()
    buildings = Building.objects.all()
    room_types = RoomType.objects.all()
    lab_types = LabType.objects.all()

    if request.method == 'POST':
        code = request.POST.get('code')
        building_id = request.POST.get('building')
        room_type_id = request.POST.get('room_type')
        lab_type_id = request.POST.get('lab_type')
        capacity = request.POST.get('capacity')
        dimensions = request.POST.get('dimensions')
        max_courses = request.POST.get('max_courses')
        proctors_required = request.POST.get('proctors_required')
        is_overflow = request.POST.get('is_overflow') == 'on'

        if all([code, building_id, room_type_id, capacity, dimensions, max_courses, proctors_required]):
            Room.objects.create(
                code=code,
                building=Building.objects.get(id=building_id),
                room_type=RoomType.objects.get(id=room_type_id),
                lab_type=LabType.objects.get(id=lab_type_id) if lab_type_id else None,
                capacity=int(capacity),
                dimensions=dimensions,
                max_courses=int(max_courses),
                proctors_required=int(proctors_required),
                is_overflow=is_overflow
            )
            return redirect('rooms')

    context = {
        'rooms': rooms,
        'buildings': buildings,
        'room_types': room_types,
        'lab_types': lab_types,
    }
    return render(request, 'timetable/rooms.html', context)


def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    buildings = Building.objects.all()
    room_types = RoomType.objects.all()
    lab_types = LabType.objects.all()

    if request.method == 'POST':
        room.code = request.POST.get('code')
        building_id = request.POST.get('building')
        room_type_id = request.POST.get('room_type')
        lab_type_id = request.POST.get('lab_type')
        room.capacity = request.POST.get('capacity')
        room.dimensions = request.POST.get('dimensions')
        room.max_courses = request.POST.get('max_courses')
        room.proctors_required = request.POST.get('proctors_required')
        room.is_overflow = request.POST.get('is_overflow') == 'on'

        if all([room.code, building_id, room_type_id, room.capacity, room.dimensions, room.max_courses, room.proctors_required]):
            room.building = Building.objects.get(id=building_id)
            room.room_type = RoomType.objects.get(id=room_type_id)
            room.lab_type = LabType.objects.get(id=lab_type_id) if lab_type_id else None
            room.save()
            return redirect('rooms')

    context = {
        'room': room,
        'buildings': buildings,
        'room_types': room_types,
        'lab_types': lab_types,
    }
    return render(request, 'timetable/edit_room.html', context)

def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    return redirect('rooms')


def courses(request):
    courses = Course.objects.all()
    all_lecturers = Lecturer.objects.all()
    all_classes = Class.objects.all()
    all_departments = Department.objects.all()
    all_course_types = CourseType.objects.all()
    all_lab_types = LabType.objects.all()

    if request.method == 'POST':
        code = request.POST.get('code')
        title = request.POST.get('title')
        course_type_id = request.POST.get('course_type')
        department_id = request.POST.get('department')
        credit_hours = request.POST.get('credit_hours')
        enrollment = request.POST.get('enrollment')
        requires_lab = request.POST.get('requires_lab') == 'on'
        lab_type_id = request.POST.get('lab_type')

        course = Course.objects.create(
            code=code,
            title=title,
            course_type_id=course_type_id,
            department_id=department_id,
            credit_hours=credit_hours,
            enrollment=enrollment,
            requires_lab=requires_lab,
            lab_type_id=lab_type_id if lab_type_id else None
        )

        # Set relationships
        course.lecturers.set(request.POST.getlist('lecturers'))
        course.classes.set(request.POST.getlist('classes'))

        return redirect('courses')

    return render(request, 'timetable/courses.html', {
        'courses': courses,
        'all_lecturers': all_lecturers,
        'all_classes': all_classes,
        'all_departments': all_departments,
        'all_course_types': all_course_types,
        'all_lab_types': all_lab_types
    })

def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    all_lecturers = Lecturer.objects.all()
    all_classes = Class.objects.all()
    all_departments = Department.objects.all()
    all_course_types = CourseType.objects.all()
    all_lab_types = LabType.objects.all()

    if request.method == 'POST':
        course.code = request.POST.get('code')
        course.title = request.POST.get('title')
        course.course_type_id = request.POST.get('course_type')
        course.department_id = request.POST.get('department')
        course.credit_hours = request.POST.get('credit_hours')
        course.enrollment = request.POST.get('enrollment')
        course.requires_lab = request.POST.get('requires_lab') == 'on'
        course.lab_type_id = request.POST.get('lab_type') if request.POST.get('lab_type') else None
        course.save()

        course.lecturers.set(request.POST.getlist('lecturers'))
        course.classes.set(request.POST.getlist('classes'))

        return redirect('courses')

    return render(request, 'timetable/edit_course.html', {
        'course': course,
        'all_lecturers': all_lecturers,
        'all_classes': all_classes,
        'all_departments': all_departments,
        'all_course_types': all_course_types,
        'all_lab_types': all_lab_types
    })

def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    return redirect('courses')



import json


def lecturers(request):
    lecturers = Lecturer.objects.all().select_related('department')
    all_departments = Department.objects.all()
    all_courses = Course.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        department_id = request.POST.get('department')
        max_courses = request.POST.get('max_courses', 4)
        is_active = request.POST.get('is_active') == 'on'
        is_proctor = request.POST.get('is_proctor') == 'on'

        # Handle JSON fields
        availability = None
        proctor_availability = None
        
        try:
            availability = json.loads(request.POST.get('availability', '{}'))
        except json.JSONDecodeError:
            availability = {"note": request.POST.get('availability')}
            
        try:
            proctor_availability = json.loads(request.POST.get('proctor_availability', '{}'))
        except json.JSONDecodeError:
            proctor_availability = {"note": request.POST.get('proctor_availability')}

        lecturer = Lecturer.objects.create(
            name=name,
            department_id=department_id,
            max_courses=max_courses,
            is_active=is_active,
            is_proctor=is_proctor,
            availability=availability,
            proctor_availability=proctor_availability
        )

        # Set many-to-many relationships
        lecturer.courses.set(request.POST.getlist('courses'))

        return redirect('lecturers')

    return render(request, 'timetable/lecturers.html', {
        'lecturers': lecturers,
        'all_departments': all_departments,
        'all_courses': all_courses
    })

def edit_lecturer(request, lecturer_id):
    lecturer = get_object_or_404(Lecturer, id=lecturer_id)
    all_departments = Department.objects.all()
    all_courses = Course.objects.all()

    if request.method == 'POST':
        lecturer.name = request.POST.get('name')
        lecturer.department_id = request.POST.get('department')
        lecturer.max_courses = request.POST.get('max_courses', 4)
        lecturer.is_active = request.POST.get('is_active') == 'on'
        lecturer.is_proctor = request.POST.get('is_proctor') == 'on'

        # Handle JSON fields
        try:
            lecturer.availability = json.loads(request.POST.get('availability', '{}'))
        except json.JSONDecodeError:
            lecturer.availability = {"note": request.POST.get('availability')}
            
        try:
            lecturer.proctor_availability = json.loads(request.POST.get('proctor_availability', '{}'))
        except json.JSONDecodeError:
            lecturer.proctor_availability = {"note": request.POST.get('proctor_availability')}

        lecturer.save()
        lecturer.courses.set(request.POST.getlist('courses'))

        return redirect('lecturers')

    return render(request, 'timetable/edit_lecturer.html', {
        'lecturer': lecturer,
        'all_departments': all_departments,
        'all_courses': all_courses
    })


def delete_lecturer(request, lecturer_id):
    lecturer = get_object_or_404(Lecturer, id=lecturer_id)
    lecturer.delete()
    return redirect('lecturers')


def classes(request):
    classes = Class.objects.select_related('department').all()
    departments = Department.objects.all()

    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name') or None
        department_id = request.POST.get('department')
        level = request.POST.get('level')
        size = request.POST.get('size')

        Class.objects.create(
            code=code,
            name=name,
            department_id=department_id,
            level=level,
            size=size
        )
        return redirect('classes')

    return render(request, 'timetable/classes.html', {
        'classes': classes,
        'departments': departments
    })

# Edit a specific class
def edit_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    departments = Department.objects.all()

    if request.method == 'POST':
        class_obj.code = request.POST.get('code')
        class_obj.name = request.POST.get('name') or None
        class_obj.department_id = request.POST.get('department')
        class_obj.level = request.POST.get('level')
        class_obj.size = request.POST.get('size')
        class_obj.save()
        return redirect('classes')

    return render(request, 'timetable/edit_class.html', {
        'class': class_obj,
        'departments': departments
    })


def delete_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    class_obj.delete()
    return redirect('classes')

from django.contrib import messages

@login_required
def send_broadcast(request):
    if not request.user.is_lecturer:
        messages.error(request, "Only lecturers can send broadcasts")
        return redirect('home')

    try:
        lecturer = Lecturer.objects.get(user=request.user)
    except Lecturer.DoesNotExist:
        messages.error(request, "Lecturer profile not found")
        return redirect('home')

    if request.method == 'POST':
        form = BroadcastForm(request.POST, request.FILES, lecturer=lecturer)
        if form.is_valid():
            broadcast = form.save(commit=False)
            broadcast.lecturer = lecturer
            broadcast.save()
            form.save_m2m()
            messages.success(request, "Broadcast sent successfully!")
            return redirect('lecturer_broadcasts') 
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = BroadcastForm(lecturer=lecturer)

    return render(request, 'timetable/send_broadcast.html', {
        'form': form,
        'lecturer': lecturer
    })

@login_required
def lecturer_broadcasts(request):
    if not request.user.is_lecturer:
        messages.error(request, "Only lecturers can view broadcasts")
        return redirect('home')

    try:
        lecturer = Lecturer.objects.get(user=request.user)
        broadcasts = Broadcast.objects.filter(lecturer=lecturer).order_by('-created_at')
    except Lecturer.DoesNotExist:
        messages.error(request, "Lecturer profile not found")
        return redirect('home')

    return render(request, 'timetable/lecturer_broadcasts.html', {
        'broadcasts': broadcasts,
        'lecturer': lecturer
    })

@login_required
def student_inbox(request):
    user = request.user
    if not user.is_student:
        return redirect('home')

    try:
        student_profile = user.student_profile
        class_code = student_profile.class_code
        registered_courses = student_profile.registered_courses.all()
    except AttributeError:
        return HttpResponse("Student profile not properly configured.", status=403)

    # Get all broadcasts for the student
    broadcasts = Broadcast.objects.filter(
        Q(
            # Broadcasts sent to all classes in courses the student is registered for
            target_classes__isnull=True,
            course__in=registered_courses,
            lecturer__lectureschedule__assigned_class__code=class_code
        ) |
        Q(
            # Broadcasts specifically targeting the student's class
            target_classes__code=class_code,
            course__in=registered_courses
        )
    ).distinct().order_by('-created_at')
    print(f"Student class: {class_code}")
    print(f"Registered courses: {list(registered_courses.values_list('code', flat=True))}")
    print(f"Found {broadcasts.count()} broadcasts")

    return render(request, 'timetable/student_inbox.html', {
        'broadcasts': broadcasts,
        'student_class': class_code
    })

@login_required
def download_attachment(request, broadcast_id):
    try:
        broadcast = Broadcast.objects.get(id=broadcast_id)
        
        # Verify student has permission to access this attachment
        if not is_student_authorized(request.user, broadcast):
            raise Http404("You don't have permission to access this file")
            
        file_path = os.path.join(settings.MEDIA_ROOT, str(broadcast.attachment))
        
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        raise Http404("File not found")
    except Broadcast.DoesNotExist:
        raise Http404("Broadcast not found")

def is_student_authorized(user, broadcast):
    """Check if student is authorized to download this attachment"""
    if not user.is_student:
        return False
    try:
        student_profile = user.student_profile
        # Check if broadcast is for student's class and courses
        return broadcast.course in student_profile.registered_courses.all() and (
            not broadcast.target_classes.exists() or
            broadcast.target_classes.filter(code=student_profile.class_code).exists())
    except AttributeError:
        return False