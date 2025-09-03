from django.db import models

class LectureSchedule(models.Model):
    course = models.ForeignKey('Timetable.Course', on_delete=models.CASCADE)
    assigned_class = models.ForeignKey('Timetable.Class', on_delete=models.CASCADE)
    lecturer = models.ForeignKey('Timetable.Lecturer', on_delete=models.CASCADE)
    room = models.ForeignKey('Timetable.Room', on_delete=models.CASCADE)
    day = models.CharField(max_length=10)  # E.g. 'Monday'
    time_slot = models.ForeignKey('Timetable.TimeSlot', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    college = models.ForeignKey(
        'Timetable.College',
        on_delete=models.CASCADE,
        related_name='lecture_schedules',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.course.code} - {self.day} - {self.time_slot}"


class ExamSchedule(models.Model):
    """Represents a scheduled exam for a course."""
    course = models.ForeignKey('Timetable.Course', on_delete=models.CASCADE)
    date = models.DateField()
    time_slot = models.ForeignKey('Timetable.TimeSlot', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    college = models.ForeignKey(
        'Timetable.College',
        on_delete=models.CASCADE,
        related_name='exam_schedules',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.course.code} - {self.date} - {self.time_slot}"


class ExamRoomAssignment(models.Model):
    """Represents a room assigned to host (part of) an exam."""
    exam = models.ForeignKey('ExamSchedule', related_name='room_assignments', on_delete=models.CASCADE)
    room = models.ForeignKey('Timetable.Room', on_delete=models.CASCADE)
    proctors = models.ManyToManyField('Timetable.Lecturer', blank=True)
    seating_manual = models.BooleanField(
        default=False,
        help_text="Enable for rooms like LectureHall-A with manual/custom seating."
    )
    college = models.ForeignKey(
        'Timetable.College',
        on_delete=models.CASCADE,
        related_name='exam_room_assignments',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.exam.course.code} - {self.room.code}"


class ExamRoomClassAllocation(models.Model):
    """Maps a class to a specific room and set of columns."""
    room_assignment = models.ForeignKey(
        'ExamRoomAssignment',
        related_name='class_allocations',
        on_delete=models.CASCADE
    )
    class_assigned = models.ForeignKey('Timetable.Class', on_delete=models.CASCADE)
    columns_used = models.JSONField(
        null=True,
        blank=True,
        help_text="List of column indexes (e.g., [0, 1, 2]) or null for manual seating."
    )
    student_count = models.PositiveIntegerField()
    college = models.ForeignKey(
        'Timetable.College',
        on_delete=models.CASCADE,
        related_name='exam_room_class_allocations',
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.class_assigned.code} in {self.room_assignment.room.code} "
            f"(cols: {self.columns_used or 'manual'})"
        )


class StudentExamAllocation(models.Model):
    """Individual student seating assignment for a particular exam."""
    student_index = models.CharField(max_length=20, db_index=True)
    exam = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE)
    room = models.ForeignKey('Timetable.Room', on_delete=models.CASCADE)
    column_number = models.PositiveIntegerField(
        help_text="0-indexed column seat number assigned to the student."
    )
    college = models.ForeignKey(
        'Timetable.College',
        on_delete=models.CASCADE,
        related_name='student_exam_allocations',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('student_index', 'exam')
        ordering = ['exam', 'room', 'column_number']

    def __str__(self):
        return (
            f"{self.student_index} → {self.exam.course.code} "
            f"in {self.room.code} (col {self.column_number})"
        )
