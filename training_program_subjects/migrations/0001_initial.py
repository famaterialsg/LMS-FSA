# Generated by Django 5.1.1 on 2024-09-07 02:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('subject', '0001_initial'),
        ('training_program', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingProgramSubjects',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training_program.trainingprogram')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subject.subject')),
            ],
            options={
                'unique_together': {('program', 'subject')},
            },
        ),
    ]
