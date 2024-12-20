# Generated by Django 5.1.1 on 2024-10-27 07:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0002_initial'),
        ('learning_path', '0002_step'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learningpath',
            name='courses',
        ),
        migrations.AddField(
            model_name='step',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='steps', to='course.course'),
        ),
    ]
