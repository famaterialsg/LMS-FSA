# Generated by Django 5.0.9 on 2024-10-16 05:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('assessments', '0001_initial'),
        ('exercises', '0001_initial'),
        ('quiz', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_assessments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='assessment',
            name='exercises',
            field=models.ManyToManyField(blank=True, related_name='assessments', to='exercises.exercise'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='quizzes',
            field=models.ManyToManyField(blank=True, related_name='assessments', to='quiz.quiz'),
        ),
    ]
