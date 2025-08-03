from django.contrib import admin
from .models import (
    Building, RoomType, LabType, Room, Department, Class, Lecturer,College,
    CourseType, Course, TimeSlot, ExamDate, ProctorAssignment,CourseRegistration,ClassStudent,Broadcast
)


admin.site.register(Building)
admin.site.register(RoomType)
admin.site.register(LabType)
admin.site.register(CourseType)
admin.site.register(ExamDate)
admin.site.register(College)
admin.site.register(ClassStudent)
admin.site.register(CourseRegistration)
admin.site.register(Broadcast)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('code', 'building', 'room_type', 'capacity', 'is_overflow')
    list_filter = ('building', 'room_type', 'is_overflow')
    search_fields = ('code',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'building')
    search_fields = ('code', 'name')


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('code', 'department', 'level', 'size')
    list_filter = ('department', 'level')
    search_fields = ('code',)


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'is_proctor', 'is_active', 'max_courses')
    list_filter = ('department', 'is_proctor', 'is_active')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'department', 'course_type', 'credit_hours', 'enrollment', 'requires_lab')
    list_filter = ('department', 'course_type', 'requires_lab')
    search_fields = ('code', 'title')
    filter_horizontal = ('lecturers', 'classes')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('code', 'start_time', 'end_time', 'is_lecture_slot', 'is_exam_slot')
    list_filter = ('is_lecture_slot', 'is_exam_slot')
    search_fields = ('code',)


@admin.register(ProctorAssignment)
class ProctorAssignmentAdmin(admin.ModelAdmin):
    list_display = ('proctor', 'exam_date', 'is_available')
    list_filter = ('exam_date', 'is_available')
    search_fields = ('proctor__name',)