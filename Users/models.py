from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from django.core.validators import RegexValidator



class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+\- ]+$',
            message='Username may contain letters, digits, spaces, and @/./+/-/_.'
        )],
    )
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
    registered_courses = models.ManyToManyField('Timetable.Course', related_name='students')
    program = models.CharField(max_length=100)
    class_code = models.CharField(max_length=20)
    secondary_email = models.EmailField(blank=True, null=True)
    college = models.ForeignKey('Timetable.College', on_delete = models.CASCADE, related_name="student_profile", blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.index_number})"

class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.CharField(max_length=100)
    secondary_email = models.EmailField(blank=True, null=True)
    college = models.ForeignKey('Timetable.College', on_delete = models.CASCADE, related_name="lecturer_profile", blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"
    

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=100, blank=True, null=True)  
    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    secondary_email = models.EmailField(blank=True, null=True)
    college = models.ForeignKey('Timetable.College', on_delete = models.CASCADE, related_name="admin_profile", blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"

class Complaint(models.Model):
    REQUEST_STATUS = [
        ('Pending', 'Pending'),
        ('Declined', 'Declined'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    college = models.ForeignKey('Timetable.College', on_delete=models.CASCADE, related_name='complaints', null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=REQUEST_STATUS, default='Pending')
    response = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto-populate college from user's profile if not explicitly set
        if self.college is None and getattr(self, 'user_id', None):
            user = self.user
            self.college = (
                getattr(getattr(user, 'student_profile', None), 'college', None)
                or getattr(getattr(user, 'lecturer_profile', None), 'college', None)
                or getattr(getattr(user, 'admin_profile', None), 'college', None)
            )
        super().save(*args, **kwargs)

    def get_conversation(self):
        conversation = []
        # Add original message
        conversation.append({
            'sender': self.user,
            'message': self.message,
            'timestamp': self.submitted_at,
            'is_admin': False
        })
        
        # Parse responses if they exist
        if self.response:
            for part in self.response.split('\n\n---\n\n'):
                if '):\n' in part:
                    sender_part, message = part.split('):\n', 1)
                    sender_name = sender_part.split(' (')[0]
                    timestamp_str = sender_part.split(' (')[1]
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                    except ValueError:
                        timestamp = self.responded_at
                    
                    # Determine if sender is admin (you may need to adjust this logic)
                    is_admin = "Admin" in sender_name
                    conversation.append({
                        'sender_name': sender_name,
                        'message': message,
                        'timestamp': timestamp,
                        'is_admin': is_admin
                    })
        
        return conversation

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.status})"