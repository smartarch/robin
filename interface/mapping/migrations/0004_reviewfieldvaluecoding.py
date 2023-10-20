# Generated by Django 4.2.6 on 2023-10-19 09:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('publication', '0001_initial'),
        ('mapping', '0003_reviewfieldvaluenumber_reviewfieldvaluetext_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewFieldValueCoding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('value', models.TextField()),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='publication.publication')),
                ('review_field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mapping.reviewfield')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]