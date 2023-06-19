# Generated by Django 4.1.7 on 2023-06-19 07:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('file_storage', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CondensedPropertyKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExperimentalResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(blank=True, max_length=500)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='file_storage.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField(blank=True, null=True)),
                ('atoms_referenced', models.TextField(blank=True)),
                ('condensed_property_key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stats.condensedpropertykey')),
            ],
        ),
        migrations.CreateModel(
            name='ParameterType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.CharField(blank=True, max_length=50)),
                ('variant', models.CharField(blank=True, max_length=50)),
                ('num_atoms_required', models.PositiveIntegerField(blank=True, null=True)),
                ('project_name', models.CharField(blank=True, max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Statistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('conformational_ensemble', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='file_storage.conformationalensemble')),
                ('parameters', models.ManyToManyField(blank=True, to='stats.parameter')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ResponseEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('values', models.JSONField()),
                ('ensemble_index', models.PositiveIntegerField(blank=True, null=True)),
                ('count', models.PositiveIntegerField(blank=True, null=True)),
                ('standard_deviation', models.FloatField(blank=True, null=True)),
                ('variance', models.FloatField(blank=True, null=True)),
                ('mean', models.FloatField(blank=True, null=True)),
                ('first_quartile', models.FloatField(blank=True, null=True)),
                ('median', models.FloatField(blank=True, null=True)),
                ('third_quartile', models.FloatField(blank=True, null=True)),
                ('mode', models.FloatField(blank=True, null=True)),
                ('minimum', models.FloatField(blank=True, null=True)),
                ('maximum', models.FloatField(blank=True, null=True)),
                ('range', models.FloatField(blank=True, null=True)),
                ('skewness', models.FloatField(blank=True, null=True)),
                ('kurtosis', models.FloatField(blank=True, null=True)),
                ('coeff_variation', models.FloatField(blank=True, null=True)),
                ('conformational_ensemble', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='file_storage.conformationalensemble')),
                ('experimental_response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stats.experimentalresponse')),
            ],
        ),
        migrations.AddField(
            model_name='parameter',
            name='parameter_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stats.parametertype'),
        ),
    ]