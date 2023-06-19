from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from file_storage.models import ConformationalEnsemble, Project
from .models import ExperimentalResponse, ResponseEntry, Statistics

@receiver(post_save, sender=Project)
def create_experimental_response(sender, instance, created, **kwargs):
    if created:
        user = instance.user  # Get the user associated with the project
        ExperimentalResponse.objects.create(project=instance, user=user)


@receiver(m2m_changed, sender=Project.conformational_ensembles.through)
def create_response_entries(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        project = instance
        experimental_response = ExperimentalResponse.objects.get(project=project)
        ensembles = list(project.conformational_ensembles.all().order_by('id'))
        for ensemble_id in pk_set:
            conformational_ensemble = ConformationalEnsemble.objects.get(id=ensemble_id)
            ensemble_index = ensembles.index(conformational_ensemble) + 1
            ResponseEntry.objects.create(
                experimental_response=experimental_response,
                conformational_ensemble=conformational_ensemble,
                ensemble_index=ensemble_index,
                values=[None],
            )

@receiver(m2m_changed, sender=Project.conformational_ensembles.through)
def delete_response_entries(sender, instance, action, pk_set, **kwargs):
    if action == 'post_remove':
        experimental_response = ExperimentalResponse.objects.get(project=instance)
        for ensemble_id in pk_set:
            ResponseEntry.objects.filter(
                experimental_response=experimental_response,
                conformational_ensemble_id=ensemble_id
            ).delete()

@receiver(post_save, sender=ResponseEntry)
def resize_response_entries(sender, instance, **kwargs):
    # Get the project linked with the instance
    project = instance.experimental_response.project

    # Get the length of the values array in the saved instance
    new_length = len(instance.values) if instance.values else 0

    # Check the length of all the other response entries in the same project
    response_entries = ResponseEntry.objects.filter(experimental_response__project=project)
    for response_entry in response_entries:
        # If the length of the current response entry is less than new_length,
        # expand the array by appending None values
        if response_entry.values and len(response_entry.values) < new_length:
            response_entry.values.extend([None] * (new_length - len(response_entry.values)))
            response_entry.save()

@receiver(pre_delete, sender=Statistics)
def delete_related_parameters(sender, instance, **kwargs):
    # instance is the Statistics object being deleted
    # Delete all related Parameter objects
    instance.parameters.all().delete()