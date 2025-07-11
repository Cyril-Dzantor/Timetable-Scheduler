# Generated by Django 5.0.3 on 2025-05-15 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department_building', models.CharField(max_length=100)),
                ('capacity', models.PositiveIntegerField()),
                ('room_code', models.CharField(max_length=20, unique=True)),
                ('room_type', models.CharField(max_length=20)),
            ],
        ),
    ]
