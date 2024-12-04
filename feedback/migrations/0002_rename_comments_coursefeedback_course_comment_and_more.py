# Generated by Django 5.0.9 on 2024-11-28 09:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0008_assessmenttype_enrollment_come_back_and_more"),
        ("feedback", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="instructorfeedback",
            name="course",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feedbacks",
                to="course.course",
            ),
        ),
    ]
