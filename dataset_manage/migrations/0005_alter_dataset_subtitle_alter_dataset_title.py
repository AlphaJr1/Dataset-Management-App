# Generated by Django 5.0.6 on 2024-06-19 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_manage', '0004_photoreview_remove_additionalinfo_photo_review_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='subtitle',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='title',
            field=models.CharField(default='', max_length=255),
        ),
    ]
