# Generated by Django 5.1.3 on 2024-12-04 16:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0011_course_discount_course_price_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssessmentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='enrollment',
            name='come_back',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='last_accessed_material',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='course.coursematerial'),
        ),
    ]