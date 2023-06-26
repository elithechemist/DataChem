import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View

from stats.functions.mlr import perform_regression_and_save_plot
from .forms import UploadFileForm
from .models import ExperimentalResponse, ResponseEntry
from file_storage.models import Project
import pandas as pd
from io import BytesIO
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from .forms import ResponseEntryForm
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from .functions.pdf_report import generate_pdf
import io
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
import numpy as np
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.cleaned_data['project']
            df = pd.read_excel(BytesIO(request.FILES['file'].read()))

            # Get all experimental responses associated with the project
            exp_responses = ExperimentalResponse.objects.filter(project=project)

            processed_indices = set()

            # For each row in the DataFrame, create a ResponseEntry
            for index, row in df.iterrows():
                if pd.isnull(row[0]):
                    raw_content = f'The molecule index is missing for values <strong>{escape(row[1:].dropna().tolist())}</strong>.'
                    formatted_content = mark_safe(raw_content)
                    messages.error(request, formatted_content)
                    continue

                try:
                    ensemble_index = int(row[0])
                except ValueError:
                    raw_content = f'The <strong>index {escape(row[0])}</strong> must be an integer.'
                    formatted_content = mark_safe(raw_content)
                    messages.error(request, formatted_content)
                    continue

                if ensemble_index in processed_indices:
                    raw_content = f'The molecule with <strong>index {escape(ensemble_index)}</strong> is duplicated.'
                    formatted_content = mark_safe(raw_content)
                    messages.error(request, formatted_content)
                    continue

                processed_indices.add(ensemble_index)

                try:
                    values = [float(value) for value in row[1:].dropna().tolist()]
                except ValueError:
                    raw_content = f'The values <strong>{escape(row[1:].dropna().tolist())}</strong> for <strong>index {escape(ensemble_index)}</strong> must be numbers.'
                    formatted_content = mark_safe(raw_content)
                    messages.error(request, formatted_content)
                    continue

                # Check if the ensemble index exists in any experimental response of the project
                if not exp_responses.filter(responseentry__ensemble_index=ensemble_index).exists():
                    raw_content = f'No molecule with <strong>index {escape(ensemble_index)}</strong> found in {escape(project.name)}.'
                    formatted_content = mark_safe(raw_content)
                    messages.error(request, formatted_content)
                    continue

                # If the ensemble index exists, then you can proceed to update the ResponseEntry
                response_entries = ResponseEntry.objects.filter(
                    experimental_response__in=exp_responses,
                    ensemble_index=ensemble_index,
                )

                # If there are multiple response entries for the same ensemble index, this could be an error too
                if response_entries.count() > 1:
                    raw_content = f'Multiple response entries found for molecule with <strong>index {escape(ensemble_index)}</strong> in {escape(project.name)}.'
                    formatted_content = mark_safe(raw_content)
                    messages.error(request, formatted_content)
                    continue

                response_entry = response_entries.first()

                if response_entry.values and not all(value is None for value in response_entry.values):
                    raw_content = f'Molecule with <strong>index {escape(ensemble_index)}</strong> already has values. Remove existing values before uploading new values.'
                    formatted_content = mark_safe(raw_content)
                    messages.error(request, formatted_content)
                    continue

                response_entry.values = values
                response_entry.save()

            if(len(messages.get_messages(request)) == 0):
                messages.success(request, 'File uploaded successfully')

            return redirect('stats:upload')
    else:
        form = UploadFileForm()

    return render(request, 'stats/upload.html', {'form': form})

def project_response_table(request, project_id=None):
    if project_id is None:
        project = Project.objects.first()  # Default to the first project
        if project is None:
            return HttpResponseBadRequest("No projects available")
    else:
        project = Project.objects.get(id=project_id)
        
    projects = Project.objects.all()  # Get all projects
    response_entries = ResponseEntry.objects.filter(experimental_response__project=project)
    molecules = set(entry.ensemble_index for entry in response_entries)
    total_molecules = max(molecules) if molecules else 0

    response_table = []
    for molecule in range(1, total_molecules + 1):
        molecule_data = {'molecule': molecule}
        molecule_entries = response_entries.filter(ensemble_index=molecule)
        for entry in molecule_entries:
            values = entry.values
            if values is None:
                values = []  # Convert None to an empty list
            molecule_data[f'exp_response_{entry.experimental_response.id}'] = values
        response_table.append(molecule_data)

    context = {'projects': projects, 'current_project': project, 'response_table': response_table, 'total_molecules': total_molecules}
    return render(request, 'stats/response_table.html', context)

from django.forms import modelformset_factory

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_values(request, project_id=None):
    print("POST_INIT: " + str(request.POST) + "\n\n")
    
    if request.method == 'POST':
        post_data = dict(request.POST.lists())
        print("POST_DATA: " + str(post_data) + "\n\n")

        # A dictionary to hold values for each ResponseEntry object
        entries_values = {}

        for key, values in post_data.items():
            if key.startswith('entry-'):
                print("KEY: " + str(key))
                print("VALUE: " + str(values))

                parts = key.split('-')
                molecule_index = int(parts[1]) - 1
                value_index = int(parts[3])

                print("MOLECULE_INDEX: " + str(molecule_index))
                print("VALUE_INDEX: " + str(value_index))

                # Single value for a single molecule
                if len(values) == 1:
                    if molecule_index not in entries_values:
                        entries_values[molecule_index] = []
                    
                    while len(entries_values[molecule_index]) <= value_index:
                        entries_values[molecule_index].append(None)
                    
                    entries_values[molecule_index][value_index] = None if values[0].strip() == "" else float(values[0])

                # Multiple values for multiple molecules
                else:
                    for i, value in enumerate(values):
                        if i not in entries_values:
                            entries_values[i] = []
                        
                        while len(entries_values[i]) <= value_index:
                            entries_values[i].append(None)
                        
                        entries_values[i][value_index] = None if value.strip() == "" else float(value)

        # Now that we have built the full array for each ResponseEntry, let's save them
        for molecule_index, values in entries_values.items():
            # Adjusting molecule_index to be 1-indexed instead of 0-indexed
            entry = ResponseEntry.objects.filter(experimental_response__project__id=project_id, ensemble_index=molecule_index + 1).first()

            # Convert empty strings to None and keep other values as is
            sanitized_values = []
            for value in values:
                if value == '':
                    sanitized_values.append(None)
                else:
                    sanitized_values.append(value)
            
            # Save the sanitized values
            entry.values = sanitized_values
            entry.save()
            print(f"Saved ENTRY: {str(entry.values)}")

    return JsonResponse({'status': 'success'})

def download_project_pdf(request, project_id=None):
    # Fetch the project instance
    project = Project.objects.get(pk=project_id)
    
    # Generate the PDF file
    pdf_bytes = generate_pdf(project_id)

    # Create a FileResponse instance to serve the file
    response = FileResponse(io.BytesIO(pdf_bytes), as_attachment=True, filename=f'{project.name} List.pdf')

    # Return the response
    return response

def ajax_get_project_data(request, project_id):
    project = Project.objects.get(id=project_id)
    response_entries = ResponseEntry.objects.filter(experimental_response__project=project)
    molecules = set(entry.ensemble_index for entry in response_entries)
    total_molecules = max(molecules) if molecules else 0

    response_table = []
    for molecule in range(1, total_molecules + 1):
        molecule_data = {'molecule': molecule}
        molecule_entries = response_entries.filter(ensemble_index=molecule)
        for entry in molecule_entries:
            values = entry.values
            if values is None:
                values = []  # Convert None to an empty list
            molecule_data[f'exp_response_{entry.experimental_response.id}'] = values
        response_table.append(molecule_data)

    return JsonResponse(response_table, safe=False)

@csrf_exempt
@require_POST
def add_column(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        response_entries = ResponseEntry.objects.filter(experimental_response__project=project)
        for response_entry in response_entries:
            if response_entry.values:
                response_entry.values.append(None)
            else:
                response_entry.values = [None]
            response_entry.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def remove_column(request, project_id):
    try:
        # Fetch the relevant response entries
        response_entries = ResponseEntry.objects.filter(experimental_response__project_id=project_id)
        
        # Remove the last column from each entry
        for entry in response_entries:
            # Make sure there's more than one item in the values list before removing
            if entry.values and len(entry.values) > 1:
                entry.values.pop()
                entry.save()
        
        # Return a JSON response indicating success
        return JsonResponse({'success': True})

    except Exception as e:
        # Return a JSON response indicating failure
        return JsonResponse({'success': False, 'error': str(e)})
    
class RegressionView(LoginRequiredMixin, TemplateView):
    template_name = 'stats/mlr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = Project.objects.filter(user=self.request.user)
        context['projects'] = projects
        return context

class PerformRegressionView(View):
    def post(self, request):
        # Decode JSON request body into python data structure
        data = json.loads(request.body)
        
        # Extract parameters from request data
        project = Project.objects.get(pk=data.get('select_project', None))
        has_interaction_terms = data.get('interaction_terms', False)
        test_ratio = float(data.get('test_ratio', 1))
        split_method = data.get('split_method', 'random')
        n_models = int(data.get('n_models', 1))
        n_iterations = int(data.get('n_iterations', 1))
        collin_criteria = float(data.get('collin_criteria', 1))
        max_parameters = int(data.get('max_parameters', 1))

        print("PROJECT: " + str(project))
        print("HAS INTERACTION_TERMS: " + str(has_interaction_terms))
        print("TEST_RATIO: " + str(test_ratio))
        print("SPLIT_METHOD: " + str(split_method))
        print("N_MODELS: " + str(n_models))
        print("N_ITERATIONS: " + str(n_iterations))
        print("COLLIN_CRITERIA: " + str(collin_criteria))
        print("MAX_PARAMETERS: " + str(max_parameters))

        # Call the perform_regression_and_save_plot function with parameters
        presigned_urls, equation_strings, training_r2_scores, q2_scores, four_fold_r2_scores, validation_r2_scores, mean_absolute_errors = perform_regression_and_save_plot(project, has_interaction_terms, test_ratio, split_method, n_models, n_iterations, collin_criteria, max_parameters)

        return JsonResponse({'urls': presigned_urls, 'equations': equation_strings, 'training_r2_scores': training_r2_scores, 'q2_scores': q2_scores, 'four_fold_r2_scores': four_fold_r2_scores, 'validation_r2_scores': validation_r2_scores, 'mean_absolute_errors': mean_absolute_errors})