# Generated by Django 4.2.1 on 2023-06-27 15:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='publicationlist',
            old_name='followers',
            new_name='subscriptions',
        ),
    ]
