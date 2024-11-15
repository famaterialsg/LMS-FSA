# Generated by Django 5.0.9 on 2024-10-31 04:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('course', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('question_type', models.CharField(choices=[('MCQ', 'Multiple Choice'), ('TF', 'True/False'), ('TEXT', 'Text Response')], default='MCQ', max_length=50)),
                ('points', models.IntegerField()),
                ('course', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='course.course')),
            ],
            options={
                'db_table': 'QuizBank',
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option_text', models.TextField()),
                ('is_correct', models.BooleanField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quiz_bank.quizbank')),
            ],
            options={
                'db_table': 'Answer',
            },
        ),
    ]