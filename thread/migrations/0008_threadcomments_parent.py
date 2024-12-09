# Generated by Django 5.1.2 on 2024-12-05 07:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thread', '0007_remove_discussionthread_is_hidden_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='threadcomments',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='thread.threadcomments'),
        ),
    ]
