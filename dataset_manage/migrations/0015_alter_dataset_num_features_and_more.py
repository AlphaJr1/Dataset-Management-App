# Generated by Django 5.0.6 on 2024-06-26 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_manage', '0014_alter_datasetfile_completeness_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='num_features',
            field=models.IntegerField(blank=True, verbose_name='Number of Features'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='num_instances',
            field=models.IntegerField(blank=True, verbose_name='Number of Instances'),
        ),
    ]