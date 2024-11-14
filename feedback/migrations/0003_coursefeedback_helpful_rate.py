# Generated by Django 5.1.1 on 2024-10-31 14:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='coursefeedback',
            name='helpful_rate',
            field=models.ManyToManyField(blank=True, related_name='helpful_rate', to=settings.AUTH_USER_MODEL),
        ),
    ]