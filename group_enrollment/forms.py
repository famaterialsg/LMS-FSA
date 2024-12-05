# enrollment/forms.py
from django import forms
from course.models import Enrollment, Course
from user.models import User

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['course']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),  # Bootstrap class added here
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()  # You can customize the queryset as needed

class AdminEnrollmentForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=True)
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )