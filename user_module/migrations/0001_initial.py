# Generated by Django 5.0.9 on 2024-09-25 02:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("module_group", "0001_initial"),
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserModule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="module_group.module",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.user"
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "module")},
            },
        ),
    ]