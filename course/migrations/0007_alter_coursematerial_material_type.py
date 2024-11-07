# Generated by Django 5.0.9 on 2024-11-06 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0006_alter_enrollment_course'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursematerial',
            name='material_type',
            field=models.CharField(choices=[('assignments', 'Assignments'), ('labs', 'Labs'), ('lectures', 'Lectures'), ('references', 'References'), ('assessments', 'Assessments')], max_length=20),
        ),
    ]
