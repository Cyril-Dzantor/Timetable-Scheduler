from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(_('school email'), unique=True)
    is_student = models.BooleanField(default=False)
    is_lecturer = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['username']
    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    index_number = models.CharField(max_length=20, unique=True, db_index=True)
    program = models.CharField(max_length=100)
    level = models.CharField(max_length=20)
    secondary_email = models.EmailField(blank=True, null=True)
    assigned_class = models.ForeignKey('Timetable.Class', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.index_number})"
    
    @property
    def class_code(self):
        return self.assigned_class.code if self.assigned_class else None

class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.CharField(max_length=100)
    secondary_email = models.EmailField(blank=True, null=True)
    lecturer = models.OneToOneField('Timetable.Lecturer', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"
    
    @property
    def lecturer_name(self):
        return self.lecturer.name if self.lecturer else None
    

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=100, blank=True, null=True)  
    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    secondary_email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"

class Complaint(models.Model):
    REQUEST_STATUS = [
        ('Pending', 'Pending'),
        ('Declined', 'Declined'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=REQUEST_STATUS, default='Pending')
    response = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.status})"