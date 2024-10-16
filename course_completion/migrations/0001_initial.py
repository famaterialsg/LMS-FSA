# Generated by Django 5.0.9 on 2024-10-16 05:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('course', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseCompletion',
            fields=[
                ('completion_id', models.AutoField(primary_key=True, serialize=False)),
                ('completion_date', models.DateTimeField(auto_now_add=True)),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course.course')),
            ],
            options={
                'db_table': 'Course_Completion',
            },
        ),
    ]
