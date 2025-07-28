from django.db import models

class College(models.Model):
    """Represents a college/faculty (e.g., College of Science)"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Building(models.Model):
    """Represents a building on campus"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    college = models.ForeignKey('College', on_delete=models.SET_NULL, null=True, blank=True, related_name='buildings')

    def __str__(self):
        return f"{self.code} - {self.name}"


class RoomType(models.Model):
    """Types of rooms (lecture hall, lab, classroom etc.)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class LabType(models.Model):
    """Types of labs (IT, Chemistry, Physics etc.)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    """Represents physical rooms in buildings"""
    code = models.CharField(max_length=20, unique=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    lab_type = models.ForeignKey(LabType, on_delete=models.SET_NULL, blank=True, null=True)
    capacity = models.PositiveIntegerField()
    dimensions = models.CharField(max_length=20)
    max_courses = models.PositiveIntegerField(default=1)
    proctors_required = models.PositiveIntegerField(default=1)
    is_overflow = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} ({self.room_type.name})"


class Department(models.Model):
    """Academic departments"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)
    college = models.ForeignKey('College', on_delete=models.SET_NULL, null=True, blank=True, related_name='departments')

    def __str__(self):
        return self.name



class Class(models.Model):
    """Student classes/groups (like CS100, OP200 etc.)"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.PositiveIntegerField()
    size = models.PositiveIntegerField()
    
    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['code']

    @property
    def student_indices(self):
        return list(self.classstudent_set.values_list('student_index', flat=True))


    def __str__(self):
        return self.code


class Lecturer(models.Model):
    """Teaching staff"""
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    availability = models.JSONField(blank=True, null=True)  # For regular teaching availability
    proctor_availability = models.JSONField(blank=True, null=True)  # For exam proctoring availability
    is_proctor = models.BooleanField(default=False)
    max_courses = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CourseType(models.Model):
    """Types of courses (lecture, lab etc.)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    """Academic courses"""
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    credit_hours = models.PositiveIntegerField()
    enrollment = models.PositiveIntegerField()
    lecturers = models.ManyToManyField(Lecturer, related_name='courses')
    classes = models.ManyToManyField(Class, related_name='courses')
    requires_lab = models.BooleanField(default=False)
    lab_type = models.ForeignKey(LabType, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['code']

    @property
    def registered_students(self):
        return list(self.courseregistration_set.values_list('student_index', flat=True))


    def __str__(self):
        return f"{self.code} - {self.title}"


class TimeSlot(models.Model):
    """Time slots for scheduling"""
    start_time = models.TimeField()
    end_time = models.TimeField()
    code = models.CharField(max_length=20, unique=True)
    is_lecture_slot = models.BooleanField(default=True)
    is_exam_slot = models.BooleanField(default=False)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class ExamDate(models.Model):
    """Specific exam dates"""
    date = models.DateField(unique=True)
    day_name = models.CharField(max_length=10)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.date} ({self.day_name})"


class ProctorAssignment(models.Model):
    """Assignment of proctors to exam dates"""
    proctor = models.ForeignKey(Lecturer, on_delete=models.CASCADE, limit_choices_to={'is_proctor': True})
    exam_date = models.ForeignKey(ExamDate, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('proctor', 'exam_date')

    def __str__(self):
        return f"{self.proctor.name} on {self.exam_date.date}"
    

class ClassStudent(models.Model):
    assigned_class = models.ForeignKey('Timetable.Class', on_delete=models.CASCADE)
    student_index = models.CharField(max_length=20, db_index=True)

    class Meta:
        unique_together = ('assigned_class', 'student_index')

    def __str__(self):
        return f"{self.student_index} in {self.assigned_class.code}"
    

class CourseRegistration(models.Model):
    course = models.ForeignKey('Timetable.Course', on_delete=models.CASCADE)
    student_index = models.CharField(max_length=20, db_index=True)

    class Meta:
        unique_together = ('course', 'student_index')

    def __str__(self):
        return f"{self.student_index} registered for {self.course.code}"
