# Generated by Django 5.0.6 on 2024-06-19 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_manage', '0002_alter_dataset_profile_graphics'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='num_features',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='subtitle',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
