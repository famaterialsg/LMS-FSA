from django.contrib import admin
from .models import Survey, SkillNeed, TrainingFeedback
# Register your models here.
admin.register(Survey)
admin.register(SkillNeed)
admin.register(TrainingFeedback)