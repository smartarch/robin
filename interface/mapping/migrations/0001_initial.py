# Generated by Django 4.2.1 on 2023-07-04 08:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('publication', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Mapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField(blank=True)),
                ('secret_key', models.TextField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('leader', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('reviewers', models.ManyToManyField(related_name='reviewer_users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PublicationList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('criteria', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('followers', models.ManyToManyField(blank=True, related_name='my_followers', to='mapping.publicationlist')),
                ('mapping', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mapping.mapping')),
                ('publications', models.ManyToManyField(blank=True, to='publication.publication')),
                ('subscriptions', models.ManyToManyField(blank=True, related_name='my_subscriptions', to='mapping.publicationlist')),
            ],
        ),
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_page_size', models.PositiveSmallIntegerField(default=25)),
                ('default_list', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mapping.publicationlist')),
                ('default_mapping', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mapping.mapping')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
