# Generated by Django 5.1.1 on 2024-10-17 09:06

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assignment", "0002_assignment_assignment_content_and_more"),
        ("course", "0002_initial"),
        ("exercises", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="assignment",
            options={
                "verbose_name": "Assignment",
                "verbose_name_plural": "Assignments",
            },
        ),
        migrations.RemoveField(
            model_name="assignment",
            name="assignment_content",
        ),
        migrations.RemoveField(
            model_name="assignment",
            name="end_date",
        ),
        migrations.RemoveField(
            model_name="assignment",
            name="start_date",
        ),
        migrations.AddField(
            model_name="assignment",
            name="content",
            field=models.TextField(
                blank=True, null=True, verbose_name="Assignment Content"
            ),
        ),
        migrations.AddField(
            model_name="assignment",
            name="course",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="course.course",
                verbose_name="Course",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="assignment",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="assignment",
            name="created_by",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_assignments",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="assignment",
            name="assignment_name",
            field=models.CharField(max_length=100, verbose_name="Assignment Name"),
        ),
        migrations.AlterField(
            model_name="assignment",
            name="coding_exercises",
            field=models.ManyToManyField(
                blank=True,
                related_name="assignments",
                to="exercises.exercise",
                verbose_name="Coding Exercises",
            ),
        ),
        migrations.CreateModel(
            name="StudentAssignmentAttempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("score", models.IntegerField(default=0, verbose_name="Score")),
                ("note", models.TextField(blank=True, null=True, verbose_name="Notes")),
                ("attempt_date", models.DateTimeField(auto_now_add=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="assignment.assignment",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Student Assignment Attempt",
                "verbose_name_plural": "Student Assignment Attempts",
            },
        ),
    ]
