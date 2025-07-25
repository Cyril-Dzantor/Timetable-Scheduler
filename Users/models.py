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

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.index_number})"

class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.CharField(max_length=100)
    secondary_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"
    

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=100, blank=True, null=True)  
    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    secondary_email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"