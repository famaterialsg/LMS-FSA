from django import forms
from .models import AIInsights, UserProgress
from .models import Course ,Enrollment
# Form for creating and editing users
class AI_InsightsForm(forms.ModelForm):
    class Meta:
        model = AIInsights
        fields = ['user', 'course', 'insight_text', 'insight_type']
        labels = {
            'insight_type': 'Insight Type (Either "Warning", "Compliment" or "Info" is prefered)'
        }

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel File")

class AI_InsightsCourseForm(forms.ModelForm):
    class Meta:
        model = AIInsights
        fields = ['course']
        labels = {
            'course': 'Choose a course to filter'
        }
        
class AIInsightsFilterForm(forms.Form):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Filter by Course"
    )
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # Lấy user từ tham số
        super().__init__(*args, **kwargs)
        # Giới hạn QuerySet cho user hiện tại
        user_enroll = Enrollment.objects.filter(student=user).values_list('course', flat=True)
        self.fields['courses'].queryset = Course.objects.filter(id__in=user_enroll)

class UserProgressForm(forms.Form):
    search_user = forms.CharField(label='Search User')

