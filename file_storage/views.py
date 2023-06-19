import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import MoleculeForm, ParameterForm, ProjectForm
from django.views.generic import ListView, FormView, DetailView
from django.conf import settings
from .models import Molecule
from file_storage.functions.openbabel import g09_to_xyz, xyz_to_smiles
from file_storage.functions.pubchem import smiles_to_iupac
from file_storage.functions.rdkit import xyz_to_indexed_svg
from file_storage.functions.get_properties import main
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
import json
import tempfile
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Project, Molecule, ConformationalEnsemble
from django.contrib.auth.mixins import LoginRequiredMixin
from chemstats.utils.storage import s3_generate_presigned_url, s3_molecule_store
import boto3
import os, time


def test(request):
    #print(g09_to_xyz("B04"))
    #print(xyz_tPo_smiles("B04"))
    #print(smiles_to_iupac("smiles=1S/C21H22N2O2/c24-18-10-16-19-13-9-17-21(6-7-22(17)11-12(13)5-8-25-16)14-3-1-2-4-15(14)23(18)20(19)21/h1-5,13,16-17,19-20H,6-11H2/t13-,16-,17-,19-,20-,21+/m0/s1"))
    #xyz_to_indexed_svg("/mnt/c/Users/elijo/OneDrive/Documents/Code/chemstats/media/xyz_files/A01.xyz")
    #main(['X', 't'], "/mnt/c/Users/elijo/OneDrive/Documents/Code/chemstats/media/log_files")

    messages.info(request, 'This is a test message.')
    return render(request, 'file_storage/test.html')

@login_required
def create_molecule(request):
    if request.method == 'POST':
        form = MoleculeForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('log_file')  # Get the list of uploaded files

            for f in files:
                new_form = MoleculeForm(request.POST, {'log_file': f})
                if new_form.is_valid():
                    # Upload file to S3
                    print("Uploading file to S3" + str(f))
                    unique_id = str(uuid.uuid4())
                    file_name = f'{unique_id}.log'
                    print(f"File name is {file_name}")
                    s3_key = s3_molecule_store(file_name, f.read())
                    print("S3 KEY: " + s3_key)
                    
                    # Create a new molecule instance and set the user
                    molecule = new_form.save(commit=False)
                    molecule.user = request.user

                    # Store the S3 key as the log_file field
                    molecule.log_file = file_name
                    molecule.save()

            return redirect('create_molecule')
    else:
        form = MoleculeForm()

    return render(request, 'file_storage/create_molecule.html', {'form': form})


class MoleculeListView(ListView):
    model = ConformationalEnsemble
    template_name = 'file_storage/molecule_posts.html'
    context_object_name = 'conformers'
    ordering = ['-date']
    paginate_by = 200

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.all()  # or apply some filter if needed

        # Generate SVG URL for each conformer
        conformers = context['conformers']
        for conformer in conformers:
            # assuming that svg_file is a field on your ConformationalEnsemble model
            conformer.svg_url = s3_generate_presigned_url(str(conformer.svg_file))

        return context

class MoleculeDetailView(FormView):
    model = ConformationalEnsemble
    template_name = 'file_storage/molecule_detail.html'
    form_class = ParameterForm

    def get_object(self, queryset=None):
        """Retrieve the object to be displayed."""
        return self.model.objects.get(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        molecule = self.get_object()

        # get the list of log files for the conformers
        log_files = [(conformer.log_file.path, conformer.log_file.name) for conformer in molecule.conformers.all()]
        self.form_class.base_fields['log_file'].choices = log_files

        # Add the SVG url for the unindexed SVG file
        svg_url = s3_generate_presigned_url(str(molecule.svg_file))
        context['svg_url'] = svg_url

        form = self.get_form()

        # Add context for the form
        context['form'] = form

        # Add context for the molecule object
        context['molecule'] = molecule

        return context
    
    def form_valid(self, form):
        # get the selected log file
        log_file_path = form.cleaned_data['log_file']

        # Convert the log file to XYZ
        xyz_file = g09_to_xyz(log_file_path)
        xyz_path = os.path.join(settings.MEDIA_ROOT, 'xyz_files', xyz_file + ".xyz")

        # Generate SVG file and save to temporary file
        svg_path = xyz_to_indexed_svg(xyz_path)

        # Add the SVG path to the context so it can be displayed in the template
        self.get_context_data()['indexed_svg_path'] = os.path.join(settings.MEDIA_URL, 'temp/', svg_path)

        # Create a temporary file to store the JSON data
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp/json_files')
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=temp_path) as tmp:
            # dump the data dictionary to the temporary file in JSON format
            json.dump(form.cleaned_data, tmp)

        molecule = self.get_object()
        # Process parameter data
        messages.success(self.request, f"Parameter has been submitted for {molecule}.")
        redirect_string = reverse_lazy('molecule_detail_redirect', kwargs={'pk': molecule.pk})
        redirect_string += f"?json_file={tmp.name}"

        # Redirect to the molecule detail page
        redirect_string = reverse_lazy('molecule_detail_redirect', kwargs={'pk': molecule.pk})
        redirect_string += f"?json_file={tmp.name}"

        self.success_url = redirect_string

        return super().form_valid(form)
    
class MoleculeDetailViewRedirect(DetailView):
    model = Molecule
    template_name = 'file_storage/molecule_detail_redirect.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        molecule = self.get_object()
        xyz_path = os.path.join(settings.MEDIA_ROOT, 'xyz_files', g09_to_xyz(molecule.log_file.path) + ".xyz")

        # Generate SVG file and save to temporary file
        svg_path = xyz_to_indexed_svg(xyz_path)

        # Add context for the molecule object
        context['molecule'] = molecule

        json_file_path = self.request.GET.get('json_file')

        # Open the json file and print its content
        with open(json_file_path, 'r') as json_file:
            json_content = json.load(json_file)

        context['json_content'] = json_content
        
        return context
    
def statistics(request):
    print("ATTEMPTING TO ACCESS STATS")
    messages.info(request, 'This page is under development. Please visit again later')
    return render(request, 'file_storage/statistics.html')

class Projects(LoginRequiredMixin, FormView):
    model = Project
    template_name = 'file_storage/projects.html'
    form_class = ProjectForm
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        context['form'] = form

        # Fetch the projects for the current user
        user_projects = Project.objects.filter(user=self.request.user)
        context['project'] = user_projects

        return context
    
    def form_valid(self, form):
        project = form.save(commit=False)
        project.user = self.request.user
        project.save()

        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('file_storage:projects')

@csrf_exempt
def add_conformational_ensemble_to_project(request):
    print("Entered add_ensemble_to_project view")
    if request.method == 'POST':
        print(request.POST)
        conformational_ensemble_id = request.POST.get('conformational_ensemble_id')
        project_id = request.POST.get('project_id')
        print(f"Adding conformational ensemble with ID: {conformational_ensemble_id}")
        print(f"Project ID: {project_id}")
        conformational_ensemble = get_object_or_404(ConformationalEnsemble, id=conformational_ensemble_id)
        project = get_object_or_404(Project, id=project_id)
        print(f"Adding conformational ensemble to project: {project.name}")
        project.conformational_ensembles.add(conformational_ensemble)
        project.save()  # Save the project after adding the conformational ensemble
        print("Conformational ensemble added successfully.")
        return JsonResponse({'status': 'success'})

@csrf_exempt
def remove_conformational_ensemble_from_project(request):
    if request.method == 'POST':
        conformational_ensemble_id = request.POST.get('conformational_ensemble_id')
        project_id = request.POST.get('project_id')
        print(f"Removing conformational ensemble with ID: {conformational_ensemble_id}")
        conformational_ensemble = get_object_or_404(ConformationalEnsemble, id=conformational_ensemble_id)
        project = get_object_or_404(Project, id=project_id)
        print(f"Removing conformational ensemble from project: {project.name}")
        project.conformational_ensembles.remove(conformational_ensemble)
        project.save()  # Save the project after removing the conformational ensemble
        print("Conformational ensemble removed successfully.")
        return JsonResponse({'status': 'success'})

def get_conformational_ensembles_in_project(request):
    project_id = request.GET.get('project_id', None)

    if project_id is not None:
        try:
            # assuming you have a Project model with a many-to-many field to ConformationalEnsembles
            project = Project.objects.get(pk=project_id)
        except:
            return JsonResponse({'error': 'Project not found'}, status=404)

        # get the IDs of the conformational ensembles in the project
        conformational_ensemble_ids = list(project.conformational_ensembles.values_list('id', flat=True))
        
        return JsonResponse(conformational_ensemble_ids, safe=False)
    
    else:
        return JsonResponse({'error': 'No project id provided'}, status=400)

def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        return redirect('projects') # or wherever you want to redirect after deleting
    return render(request, 'file_storage/confirm_delete.html', {'object': project})


def view_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    conformational_ensembles = project.conformational_ensembles.all() # assuming your Project model has a many-to-many relationship with a Molecule model
    
    # Generate SVG URL for each conformer
    for conformer in conformational_ensembles:
        # assuming that svg_file is a field on your ConformationalEnsemble model
        conformer.svg_url = s3_generate_presigned_url(str(conformer.svg_file))

    return render(request, 'file_storage/view_project.html', {'project': project, 'conformational_ensembles': conformational_ensembles})


@login_required
def parameter_view(request, parameter_name, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    molecules = project.molecules.all()

    return render(request, 'file_storage/parameters.html', {'parameter_name': parameter_name, 'project_id': project_id, molecules: 'molecules'})
