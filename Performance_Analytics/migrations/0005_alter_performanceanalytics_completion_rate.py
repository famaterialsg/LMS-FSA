# Generated by Django 5.0.1 on 2024-10-15 04:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance_analytics', '0004_rename_course_performanceanalytics_course_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='performanceanalytics',
            name='completion_rate',
            field=models.IntegerField(default=0.0),
        ),
    ]
