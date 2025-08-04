from django.contrib import admin
from .models import PersonalEvent,PersonalEventType,PersonalTimetable
# Register your models here.
admin.site.register (PersonalTimetable)
admin.site.register(PersonalEvent)
admin.site.register(PersonalEventType)