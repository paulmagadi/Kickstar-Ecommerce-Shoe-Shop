# Generated by Django 5.1.7 on 2025-04-12 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_emailverificationtoken'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='old_cart',
        ),
    ]
