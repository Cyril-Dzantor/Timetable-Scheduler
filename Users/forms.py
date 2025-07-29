from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .models import StudentProfile, LecturerProfile, AdminProfile,User,Complaint 

class CustomLoginForm(forms.Form):
    email = forms.EmailField(label="School Email", required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    identifier = forms.CharField(label="Index Number / Staff ID", required=True)
    is_student = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        identifier = cleaned_data.get('identifier')
        is_student = cleaned_data.get('is_student')

        if not email:
            raise forms.ValidationError("Email is required.")
        email = email.lower()

        if not password:
            raise forms.ValidationError("Password is required.")

        if not identifier:
            raise forms.ValidationError("Index Number / Staff ID is required.")

        user = authenticate(username=email, password=password)
        if user is None:
            raise forms.ValidationError("Invalid email or password.")

        if user.is_student:
            try:
                if user.student_profile.index_number != identifier:
                    raise forms.ValidationError("Index number mismatch.")
            except StudentProfile.DoesNotExist:
                raise forms.ValidationError("Student profile not found.")
        elif user.is_lecturer:
            try:
                if user.lecturer_profile.staff_id != identifier:
                    raise forms.ValidationError("Staff ID mismatch.")
            except LecturerProfile.DoesNotExist:
                raise forms.ValidationError("Lecturer profile not found.")
        elif user.is_admin:
            try:
                if user.admin_profile.staff_id != identifier:
                    raise forms.ValidationError("Staff ID mismatch.")
            except AdminProfile.DoesNotExist:
                raise forms.ValidationError("Admin profile not found.")

        self.user_cache = user
        return cleaned_data

    def get_user(self):
        return self.user_cache

class CustomRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    is_student = forms.BooleanField(required=False, widget=forms.HiddenInput())
    is_lecturer = forms.BooleanField(required=False, widget=forms.HiddenInput())
    is_admin = forms.BooleanField(required=False, widget=forms.HiddenInput())

    secondary_email = forms.EmailField(required=True)
    index_number = forms.CharField(required=False)
    program = forms.CharField(required=False)
    level = forms.CharField(required=False)
    staff_id = forms.CharField(required=False)
    department = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        is_student = cleaned_data.get('is_student')
        is_lecturer = cleaned_data.get('is_lecturer')
        is_admin = cleaned_data.get('is_admin')

        if not password or not confirm_password:
            raise forms.ValidationError("Both password fields are required.")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        if is_student and not cleaned_data.get('index_number'):
            raise forms.ValidationError("Index number is required for students.")
        if is_lecturer and not cleaned_data.get('staff_id'):
            raise forms.ValidationError("Staff ID is required for lecturers.")
        if is_admin and not cleaned_data.get('staff_id'):
            raise forms.ValidationError("Staff ID is required for admins.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_student = self.cleaned_data.get('is_student', False)
        user.is_lecturer = self.cleaned_data.get('is_lecturer', False)
        user.is_admin = self.cleaned_data.get('is_admin', False)

        if commit:
            user.save()
            if user.is_student:
                StudentProfile.objects.create(
                    user=user,
                    index_number=self.cleaned_data['index_number'],
                    program=self.cleaned_data['program'],
                    level=self.cleaned_data['level'],
                    secondary_email=self.cleaned_data['secondary_email']
                )
            elif user.is_lecturer:
                LecturerProfile.objects.create(
                    user=user,
                    staff_id=self.cleaned_data['staff_id'],
                    department=self.cleaned_data['department'],
                    secondary_email=self.cleaned_data['secondary_email']
                )
            elif user.is_admin:
                AdminProfile.objects.create(
                    user=user,
                    staff_id=self.cleaned_data['staff_id'],
                    department=self.cleaned_data['department'],
                    secondary_email=self.cleaned_data['secondary_email']
                )
        return user

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'message']