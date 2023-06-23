from django.urls import path, include
from .views import create_molecule, libraries_view, statistics, add_conformational_ensemble_to_project, remove_conformational_ensemble_from_project, get_conformational_ensembles_in_project, delete_project, view_project
from .views import MoleculeListView, MoleculeDetailView, MoleculeDetailViewRedirect, Projects

app_name = 'file_storage'

urlpatterns = [
    path('upload_data/', create_molecule, name='upload_data'),
    path('home/', MoleculeListView.as_view(), name='home'),
    path('home/<int:pk>/', MoleculeDetailView.as_view(), name='molecule_detail'),
    path('home/<int:pk>/info', MoleculeDetailViewRedirect.as_view(), name='molecule_detail_redirect'),
    path('statistics/', statistics, name='statistics'),
    path('projects/', Projects.as_view(), name='projects'),
    path('project/<int:pk>/', view_project, name='view_project'),
    path('project/<int:pk>/delete/', delete_project, name='delete_project'),
    path('get_conformational_ensembles_in_project/', get_conformational_ensembles_in_project, name='get_conformational_ensembles_in_project'),
    path('add_conformational_ensemble_to_project/', add_conformational_ensemble_to_project, name='add_conformational_ensemble_to_project'),
    path('remove_conformational_ensemble_from_project/', remove_conformational_ensemble_from_project, name='remove_conformational_ensemble_from_project'),
    path('parameters/', include('file_storage.parameter_urls')),
    path('libraries/', libraries_view, name='libraries'),
]