# Generated by Django 5.1.1 on 2024-10-25 14:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('course', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerformanceAnalytics',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('average_score', models.FloatField(default=0.0)),
                ('completion_rate', models.IntegerField(default=0.0)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course.course')),
            ],
            options={
                'db_table': 'performance',
            },
        ),
    ]