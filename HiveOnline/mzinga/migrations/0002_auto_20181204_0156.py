# Generated by Django 2.1.2 on 2018-12-04 01:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mzinga', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='id',
            field=models.UUIDField(default=uuid.UUID('ce3bb669-b8cb-4f68-b8e2-d3c53534c53d'), editable=False, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='player_2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='p2', to=settings.AUTH_USER_MODEL),
        ),
    ]
