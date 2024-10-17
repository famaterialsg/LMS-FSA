from django import forms
from .models import StudentPerformance


# Form for creating and editing StudentPerformance records
class StudentPerformanceForm(forms.ModelForm):
    class Meta:
        model = StudentPerformance
        fields = ['user', 'course', 'quiz', 'assignment', 'score', 'feedback']  # Use actual field names

