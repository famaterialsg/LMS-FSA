from django.db import models
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField
# Create your models here.

class ProgrammingLanguage(models.Model):
    language = models.CharField(primary_key=True, max_length=50, unique=True)

    def __str__(self):
        return self.language

class Exercise(models.Model):
    # LANGUAGE_CHOICES = [
    #     ('python', 'Python'),
    #     ('java', 'Java'),
    #     ('c', 'C'),
    # ]

    title = models.CharField(max_length=200)
    description = RichTextUploadingField(config_name="default", null=True)
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
    # language = models.CharField(max_length=10,
    #                             choices=LANGUAGE_CHOICES,
    #                             default='python')
    setup = models.TextField(help_text="Setup code for hard exercises", null=True, blank=True)
    test_cases = models.TextField(help_text="Define test cases as Python/Java/C code")

    def __str__(self):
        return self.title

from assessments.models import Assessment

class Submission(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  # Allow null for user
    email = models.EmailField(null=True, blank=True)  # For anonymous users
    code = models.TextField()
    # created_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.title}"
