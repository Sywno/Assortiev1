# Generated by Django 4.2.13 on 2024-06-10 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sorties', '0014_dateproposee_alter_sortieproposee_date_vote_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='photo',
            field=models.ImageField(blank=True, default='profile_pics/default_profile.jpg', null=True, upload_to='profile_pics/'),
        ),
    ]