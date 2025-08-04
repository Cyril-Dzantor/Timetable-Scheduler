from django import forms
from .models import PersonalEvent, PersonalTimetable
from Timetable.models import TimeSlot  # Note: lowercase 'timetable' to match your app name

class PersonalEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Apply Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name == 'is_recurring':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        
        # Special field adjustments
        self.fields['description'].widget.attrs.update({'rows': 3, 'placeholder': 'Optional description'})
        self.fields['location'].widget.attrs.update({'placeholder': 'e.g., Room 101 or Online'})
        
        # Filter time slots if needed
        if user:
            self.fields['time_slot'].queryset = TimeSlot.objects.all().order_by('start_time')

    class Meta:
        model = PersonalEvent
        fields = [
            'title', 'event_type', 'day', 'time_slot',
            'location', 'description', 'is_recurring', 'recurring_pattern'
        ]
        widgets = {
            'description': forms.Textarea,
            'day': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'recurring_pattern': 'Repeat every',
        }

class TimetableSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to settings form
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-select'})

    class Meta:
        model = PersonalTimetable
        fields = ['show_institutional_classes', 'show_exams', 'default_view']
        labels = {
            'show_institutional_classes': 'Show my institutional classes',
            'show_exams': 'Show my exam schedule',
            'default_view': 'Default view mode'
        }