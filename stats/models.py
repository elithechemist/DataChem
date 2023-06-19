from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
from file_storage.models import ConformationalEnsemble, Project
import numpy as np
from scipy.stats import mode, skew, kurtosis
    
class ExperimentalResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=500, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.project.name} Experimental Response'

class ResponseEntry(models.Model):
    experimental_response = models.ForeignKey(ExperimentalResponse, on_delete=models.CASCADE)
    conformational_ensemble = models.ForeignKey(ConformationalEnsemble, on_delete=models.CASCADE)
    values = models.JSONField()  # Use this to store an array of numbers
    ensemble_index = models.PositiveIntegerField(blank=True, null=True)

    # Optional statistics
    count = models.PositiveIntegerField(blank=True, null=True)
    standard_deviation = models.FloatField(blank=True, null=True)
    variance = models.FloatField(blank=True, null=True)
    mean = models.FloatField(blank=True, null=True)
    first_quartile = models.FloatField(blank=True, null=True)
    median = models.FloatField(blank=True, null=True)
    third_quartile = models.FloatField(blank=True, null=True)
    mode = models.FloatField(blank=True, null=True)
    minimum = models.FloatField(blank=True, null=True)
    maximum = models.FloatField(blank=True, null=True)
    range = models.FloatField(blank=True, null=True)
    skewness = models.FloatField(blank=True, null=True)
    kurtosis = models.FloatField(blank=True, null=True)
    coeff_variation = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Get the project from the experimental response
        project = self.experimental_response.project

        # Get the conformational ensembles in the project, ordered by id
        ensembles = list(project.conformational_ensembles.all().order_by('id'))

        # Check if the conformational ensemble is associated with the project
        if self.conformational_ensemble not in ensembles:
            raise ValidationError('The conformational ensemble is not associated with the project.')

        # Set the ensemble_index based on the number of existing ResponseEntry for the same experimental_response
        # but only for new objects (not yet saved to the database)
        if self.pk is None:
            previous_entries = ResponseEntry.objects.filter(experimental_response=self.experimental_response).count()
            self.ensemble_index = previous_entries + 1

        # first, ensure the values are a numpy array
        values = np.array([x for x in self.values if x is not None], dtype=float)

        # calculate the statistics
        self.count = len(values)
        self.minimum = np.min(values) if self.count > 0 else None
        self.maximum = np.max(values) if self.count > 0 else None
        self.range = np.ptp(values) if self.count > 0 else None
        self.mean = np.mean(values) if self.count > 0 else None
        self.first_quartile = np.percentile(values, 25) if self.count > 0 else None
        self.median = np.median(values) if self.count > 0 else None
        self.third_quartile = np.percentile(values, 75) if self.count > 0 else None
        self.mode = mode(values).mode[0] if self.count > 0 else None
        self.standard_deviation = np.std(values) if self.count > 1 else None
        self.variance = np.var(values) if self.count > 1 else None
        self.skewness = skew(values) if self.count > 1 else None
        self.kurtosis = kurtosis(values) if self.count > 1 else None
        self.coeff_variation = self.standard_deviation / self.mean if self.mean != 0 and self.count > 1 else None

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.experimental_response.project.name} Entry #{self.ensemble_index}: {self.values}'
    

class CondensedPropertyKey(models.Model):
    name = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f'{self.name}'

class ParameterType(models.Model):
    group = models.CharField(max_length=50, blank=True)
    variant = models.CharField(max_length=50, blank=True)
    num_atoms_required = models.PositiveIntegerField(blank=True, null=True)
    project_name = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        if self.variant == '' and self.project_name == '':
            return f'{self.group}'
        elif self.variant == '':
            return f'{self.group}: {self.project_name}'
        else:
            return f'{self.group} - {self.variant}: {self.project_name}'

class Parameter(models.Model):
    condensed_property_key = models.ForeignKey(CondensedPropertyKey, on_delete=models.CASCADE)
    parameter_type = models.ForeignKey(ParameterType, on_delete=models.CASCADE)
    value = models.FloatField(blank=True, null=True)
    atoms_referenced = models.TextField(blank=True)

    def __str__(self):
        return f'{self.parameter_type.project_name}: {self.parameter_type.group} - {self.parameter_type.variant}. VALUE: {self.value}. ATOMS: {self.atoms_referenced}'

class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    parameters = models.ManyToManyField(Parameter, blank=True)
    conformational_ensemble = models.ForeignKey(ConformationalEnsemble, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.conformational_ensemble.database_id} Statistics'
