from django import forms
from .models import Broadcast, Lecturer, Course, Class

# class BroadcastForm(forms.ModelForm):
#     class Meta:
#         model = Broadcast  
#         fields = '__all__'  # Or list specific fields like ['course', 'title', 'message', etc.]
    
#     def __init__(self, *args, **kwargs):
#         self.lecturer = kwargs.pop('lecturer', None)
#         super().__init__(*args, **kwargs)
        
#         if self.lecturer:
#             self.fields['course'].queryset = self.lecturer.courses.all()
#             self.fields['target_classes'].queryset = Class.objects.filter(
#                 lectureschedule__lecturer=self.lecturer
#             ).distinct()

#     def clean(self):
#         cleaned_data = super().clean()
#         if not self.lecturer:
#             return cleaned_data
            
#         # Validate course
#         course = cleaned_data.get('course')
#         if course and course not in self.lecturer.courses.all():
#             self.add_error('course', "You don't teach this course")
        
#         # Validate classes
#         target_classes = cleaned_data.get('target_classes', [])
#         valid_classes = Class.objects.filter(
#             lectureschedule__lecturer=self.lecturer
#         ).distinct()
        
#         for class_obj in target_classes:
#             if class_obj not in valid_classes:
#                 self.add_error('target_classes', 
#                     f"You're not assigned to teach {class_obj}")
#                 break
                
#         return cleaned_data
    
from django import forms
from .models import Broadcast, Course, Class

class BroadcastForm(forms.ModelForm):
    class Meta:
        model = Broadcast
        exclude = ['lecturer', 'created_at']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        self.lecturer = kwargs.pop('lecturer', None)
        super().__init__(*args, **kwargs)
        
        if self.lecturer:
            # Get courses through the Lecturer model's reverse relation
            self.fields['course'].queryset = Course.objects.filter(
                lecturers=self.lecturer
            )
            
            # Get classes through the Course-Class relationship
            self.fields['target_classes'].queryset = Class.objects.filter(
                courses__lecturers=self.lecturer
            ).distinct()