# Generated by Django 5.1.1 on 2024-11-07 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentanswer',
            name='selected_option',
        ),
        migrations.AddField(
            model_name='studentanswer',
            name='selected_options',
            field=models.ManyToManyField(blank=True, to='quiz.answeroption'),
        ),
    ]
