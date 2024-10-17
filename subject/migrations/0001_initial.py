# Generated by Django 5.0.9 on 2024-10-16 05:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('code', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('material_type', models.CharField(choices=[('assignments', 'Assignments'), ('labs', 'Labs'), ('lectures', 'Lectures'), ('references', 'References')], max_length=20)),
                ('file', models.FileField(upload_to='')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materials', to='subject.subject')),
            ],
        ),
    ]
