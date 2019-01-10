# Generated by Django 2.1.2 on 2018-12-04 19:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mzinga', '0008_auto_20181204_1955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='current_turn',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='game',
            name='id',
            field=models.UUIDField(default=uuid.UUID('993e800a-ada9-49fb-9d4a-f66c5c023b64'), editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]