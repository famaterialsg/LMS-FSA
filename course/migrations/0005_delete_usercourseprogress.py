# Generated by Django 5.0.9 on 2024-11-13 08:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0004_enrollment_date_unenrolled_enrollment_is_active"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserCourseProgress",
        ),
    ]