from django.db import models
from Users.models import User  # or your custom user model
from Scheduler.models import LectureSchedule, ExamSchedule
from Timetable.models import TimeSlot

class PersonalEventType(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#4287f5')  # Hex color
    icon = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Personal Event Type"
        verbose_name_plural = "Personal Event Types"

    def __str__(self):
        return self.name

class PersonalEvent(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    event_type = models.ForeignKey(PersonalEventType, on_delete=models.SET_NULL, null=True)
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    location = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.CharField(max_length=20, blank=True, null=True)
    linked_schedule = models.ForeignKey(LectureSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    linked_exam = models.ForeignKey(ExamSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'time_slot__start_time']
        verbose_name = "Personal Event"
        verbose_name_plural = "Personal Events"

    def __str__(self):
        return f"{self.title} ({self.day} {self.time_slot})"

class PersonalTimetable(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    show_institutional_classes = models.BooleanField(default=True)
    show_exams = models.BooleanField(default=True)
    default_view = models.CharField(max_length=10, default='week', choices=[
        ('day', 'Day View'),
        ('week', 'Week View'),
        ('month', 'Month View')
    ])
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Personal Timetable"
        verbose_name_plural = "Personal Timetables"

    def __str__(self):
        return f"Timetable for {self.user}"