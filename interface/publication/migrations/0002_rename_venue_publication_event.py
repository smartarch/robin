# Generated by Django 4.2.1 on 2023-06-02 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publication', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='publication',
            old_name='venue',
            new_name='event',
        ),
    ]
