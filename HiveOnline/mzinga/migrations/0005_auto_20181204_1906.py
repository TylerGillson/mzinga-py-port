# Generated by Django 2.1.2 on 2018-12-04 19:06

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mzinga', '0004_auto_20181204_1902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='id',
            field=models.UUIDField(default=uuid.UUID('034bd82d-d5a1-4af9-a0e9-d737778d9a65'), editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
