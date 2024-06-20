# Generated by Django 4.2.13 on 2024-06-12 09:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sorties', '0015_alter_profile_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='propositionsortie',
            name='createur',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]