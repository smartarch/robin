# Generated by Django 5.0.4 on 2024-04-18 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publication', '0006_remove_affiliation_first_created_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='authors',
            field=models.ManyToManyField(related_name='published_papers', to='publication.author'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='keywords',
            field=models.ManyToManyField(related_name='keywords', to='publication.keyword'),
        ),
    ]