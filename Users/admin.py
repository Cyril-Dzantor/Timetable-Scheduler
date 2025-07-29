from django.contrib import admin
from .models import User,StudentProfile,LecturerProfile,AdminProfile,Complaint

# Register your models here.
admin.site.register(User)
admin.site.register(StudentProfile)
admin.site.register(LecturerProfile)
admin.site.register(AdminProfile)
admin.site.register(Complaint)