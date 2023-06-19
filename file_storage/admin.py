from django.contrib import admin
from .models import Molecule, Project, ConformationalEnsemble, ComputationalMethod, Library

admin.site.register(Molecule)
admin.site.register(Project)
admin.site.register(ConformationalEnsemble)
admin.site.register(ComputationalMethod)
admin.site.register(Library)