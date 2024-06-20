# Generated by Django 4.2.13 on 2024-06-05 12:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sorties', '0013_alter_groupeamis_membres'),
    ]

    operations = [
        migrations.CreateModel(
            name='DateProposee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.AlterField(
            model_name='sortieproposee',
            name='date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vote', models.BooleanField(default=False)),
                ('date_proposee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sorties.dateproposee')),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PropositionSortie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('lieu', models.CharField(max_length=100)),
                ('dates_proposees', models.ManyToManyField(related_name='propositions', to='sorties.dateproposee')),
                ('groupe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sorties.groupeamis')),
            ],
        ),
        migrations.AddField(
            model_name='dateproposee',
            name='proposition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dates', to='sorties.propositionsortie'),
        ),
    ]
