# Generated by Django 4.2.6 on 2023-10-24 18:47
# Updated by MT to migrate existing data

from django.db import migrations, models
import django.db.models.deletion


def set_mapping(apps, schema_editor):
    ReviewField = apps.get_model('mapping', 'ReviewField')
    for field in ReviewField.objects.all():
        field.mapping = field.publication_list.mapping
        field.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0006_alter_reviewfieldvaluetext_publication'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewfield',
            name='mapping',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='mapping.mapping'),
            preserve_default=False,
        ),
        migrations.RunPython(set_mapping),
        migrations.RemoveField(
            model_name='reviewfield',
            name='publication_list',
        ),
    ]