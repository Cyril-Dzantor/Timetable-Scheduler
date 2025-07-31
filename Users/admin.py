from django.contrib import admin
from .models import User, StudentProfile, LecturerProfile, AdminProfile, Complaint

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_student', 'is_lecturer', 'is_admin', 'is_active']
    list_filter = ['is_student', 'is_lecturer', 'is_admin', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'index_number', 'program', 'level', 'assigned_class']
    list_filter = ['level', 'assigned_class', 'program']
    search_fields = ['user__email', 'index_number', 'user__first_name', 'user__last_name']
    ordering = ['index_number']

@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'staff_id', 'department', 'lecturer']
    list_filter = ['department', 'lecturer']
    search_fields = ['user__email', 'staff_id', 'user__first_name', 'user__last_name', 'lecturer__name']
    ordering = ['staff_id']

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'staff_id', 'department']
    list_filter = ['department']
    search_fields = ['user__email', 'staff_id', 'user__first_name', 'user__last_name']
    ordering = ['staff_id']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'status', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__email', 'title', 'message']
    ordering = ['-submitted_at']
    readonly_fields = ['submitted_at']