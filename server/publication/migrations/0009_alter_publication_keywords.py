# Generated by Django 5.0.4 on 2024-04-18 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publication', '0008_alter_publication_keywords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='keywords',
            field=models.ManyToManyField(related_name='related_papers', to='publication.keyword'),
        ),
    ]
