# survey_app/forms.py

from django import forms
from .models import Survey, SkillNeed, TrainingFeedback

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ["staffing_needs", "skill_needs", "training_feedback"]

class SkillNeedForm(forms.ModelForm):
    class Meta:
        model = SkillNeed
        fields = ["skill_name", "level"]

class TrainingFeedbackForm(forms.ModelForm):
    class Meta:
        model = TrainingFeedback
        fields = ["feedback"]
