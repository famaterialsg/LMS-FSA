
# Generated by Django 5.0.9 on 2024-10-03 07:48

import django.db.models.deletion
from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_name', models.CharField(max_length=255)),
                ('course_description', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),

                ('course_picture_url', models.URLField(blank=True, max_length=500, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),

            ],
        ),
        migrations.CreateModel(
            name='UserCourseProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progress_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('last_accessed', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course.course')),

                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),

            ],
            options={
                'unique_together': {('user', 'course')},
            },
        ),
    ]
