# Generated by Django 4.2.6 on 2023-11-07 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publication', '0003_remove_fulltext_address_remove_fulltext_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fulltextaccess',
            name='status',
            field=models.CharField(choices=[('E', 'Empty'), ('N', 'Not Found'), ('D', 'Downloaded'), ('U', 'Uploaded')], default='E', max_length=1),
        ),
    ]
