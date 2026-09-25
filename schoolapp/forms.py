from django import forms
from .models import Student, Teacher, Staff

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["name", "roll_no", "class_name", "email"]

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["name", "subject", "email"]

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ["name", "designation", "contact"]
        
from django import forms
from django.forms import modelformset_factory
from .models import Result, Teacher

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['subject', 'marks_obtained', 'total_marks', 'grade']

class SalaryForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['basic_salary', 'allowances', 'deductions', ]

# Formset for multiple results
ResultFormSet = modelformset_factory(Result, form=ResultForm, extra=0)


