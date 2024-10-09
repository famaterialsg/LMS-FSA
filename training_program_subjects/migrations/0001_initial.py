# Generated by Django 5.0.9 on 2024-10-09 09:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("subject", "0001_initial"),
        ("training_program", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrainingProgramSubjects",
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
                (
                    "semester",
                    models.IntegerField(
                        choices=[
                            (1, "Semester 1"),
                            (2, "Semester 2"),
                            (3, "Semester 3"),
                            (4, "Semester 4"),
                            (5, "Semester 5"),
                            (6, "Semester 6"),
                            (7, "Semester 7"),
                            (8, "Semester 8"),
                            (9, "Semester 9"),
                        ],
                        default=1,
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="training_program.trainingprogram",
                    ),
                ),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="subject.subject",
                    ),
                ),
            ],
            options={
                "unique_together": {("program", "subject", "semester")},
            },
        ),
    ]
