# Generated by Django 5.0.6 on 2024-06-23 10:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_manage', '0010_datasetview'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='dataset_manage.dataset')),
            ],
        ),
    ]
