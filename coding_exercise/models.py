# Create your models here.
from django.db import models
from django.conf import settings
from user.models import User


class ProgrammingLanguage(models.Model):
    name = models.CharField(max_length=50)
    # slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
# Create your models here.
class Exercise(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('java', 'Java'),
        ('c', 'C'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    language = models.CharField(max_length=10,
                                choices=LANGUAGE_CHOICES,
                                default='python')
    test_cases = models.TextField(help_text="Define test cases as Python/Java/C code")

    def __str__(self):
        return self.title

class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    code = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.exercise.title}"


