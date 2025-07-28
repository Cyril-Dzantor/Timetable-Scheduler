from django.shortcuts import render,HttpResponse,redirect
from django.shortcuts import get_object_or_404
from .models import Room,Class,Lecturer,Course,Building, RoomType, LabType,Department


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
    all_courses = Course.objects.all()

    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        course_title = request.POST.get('course_title')
        credit_hours = request.POST.get('credit_hours')
        department = request.POST.get('department')
        students_enrolled = request.POST.get('students_enrolled')

        course = Course.objects.create(
            course_code=course_code,
            course_title=course_title,
            credit_hours=credit_hours,
            department=department,
            students_enrolled=students_enrolled
        )

        # Set relationships
        course.lecturers.set(request.POST.getlist('lecturers'))
        course.classes.set(request.POST.getlist('classes'))
        course.course_prerequisites.set(request.POST.getlist('course_prerequisites'))

        return redirect('courses')

    return render(request, 'timetable/courses.html', {
        'courses': courses,
        'all_lecturers': all_lecturers,
        'all_classes': all_classes,
        'all_courses': all_courses
    })

def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    all_lecturers = Lecturer.objects.all()
    all_classes = Class.objects.all()
    all_courses = Course.objects.exclude(id=course_id)

    if request.method == 'POST':
        course.course_code = request.POST.get('course_code')
        course.course_title = request.POST.get('course_title')
        course.credit_hours = request.POST.get('credit_hours')
        course.department = request.POST.get('department')
        course.students_enrolled = request.POST.get('students_enrolled')
        course.save()

        course.lecturers.set(request.POST.getlist('lecturers'))
        course.classes.set(request.POST.getlist('classes'))
        course.course_prerequisites.set(request.POST.getlist('course_prerequisites'))

        return redirect('courses')

    return render(request, 'timetable/edit_course.html', {
        'course': course,
        'all_lecturers': all_lecturers,
        'all_classes': all_classes,
        'all_courses': all_courses
    })

def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    return redirect('courses')



import json

def lecturers(request):
    lecturers = Lecturer.objects.all()
    all_courses = Course.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        department = request.POST.get('department')
        office_location = request.POST.get('office_location')
        max_courses = request.POST.get('max_courses') or 4
        availability_raw = request.POST.get('availability')
        is_active = True if request.POST.get('is_active') == 'on' else False

        availability = None
        if availability_raw:
            try:
                availability = json.loads(availability_raw)
            except json.JSONDecodeError:
                availability = {"note": availability_raw}

        lecturer = Lecturer.objects.create(
            name=name,
            department=department,
            office_location=office_location,
            max_courses=max_courses,
            availability=availability,
            is_active=is_active
        )

        selected_courses = request.POST.getlist('courses')
        if selected_courses:
            lecturer.courses.set(selected_courses)

        return redirect('lecturers')

    return render(request, 'timetable/lecturers.html', {
        'lecturers': lecturers,
        'all_courses': all_courses
    })


def edit_lecturer(request, lecturer_id):
    lecturer = get_object_or_404(Lecturer, id=lecturer_id)
    all_courses = Course.objects.all()

    if request.method == 'POST':
        lecturer.name = request.POST.get('name')
        lecturer.department = request.POST.get('department')
        lecturer.office_location = request.POST.get('office_location')
        lecturer.max_courses = request.POST.get('max_courses') or 4
        lecturer.is_active = True if request.POST.get('is_active') == 'on' else False

        availability_raw = request.POST.get('availability')
        if availability_raw:
            try:
                lecturer.availability = json.loads(availability_raw)
            except json.JSONDecodeError:
                lecturer.availability = {"note": availability_raw}
        else:
            lecturer.availability = None

        lecturer.save()

        selected_courses = request.POST.getlist('courses')
        lecturer.courses.set(selected_courses)

        return redirect('lecturers')

    return render(request, 'timetable/edit_lecturer.html', {
        'lecturer': lecturer,
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




