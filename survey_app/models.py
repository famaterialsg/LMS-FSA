from django.db import models

# Create your models here.
# survey_app/models.py

from user.models import User
from django.db import models
from department.models import Department

class Survey(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    staffing_needs = models.IntegerField()
    skill_needs = models.TextField()
    training_feedback = models.TextField()
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_surveys")

class SkillNeed(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    skill_name = models.CharField(max_length=255)
    level = models.CharField(max_length=50, choices=[("basic", "Basic"), ("intermediate", "Intermediate"), ("advanced", "Advanced")])

class TrainingFeedback(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    feedback = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
