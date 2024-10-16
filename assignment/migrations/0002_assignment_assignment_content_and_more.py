# Generated by Django 5.0.9 on 2024-10-16 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignment', '0001_initial'),
        ('exercises', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='assignment_content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='coding_exercises',
            field=models.ManyToManyField(blank=True, to='exercises.exercise'),
        ),
    ]
