import os
import json
import sys
import pandas as pd
import django
import logging

# Add the parent directory to the Python path (update as necessary)
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_path)

# Set the Django settings module environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chemstats.settings")

# Initialize Django
django.setup()

from stats.models import CondensedPropertyKey, ParameterType, Parameter, Statistics, ConformationalEnsemble
from django.contrib.auth.models import User

print("Imports complete. Starting script...\n")

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load phosphorous indices
file_path = os.path.join(script_dir, 'phosphorous_indices.json')
with open(file_path, 'r') as f:
    phosphorous_indices = json.load(f)

print("Loaded phosphorous indices.")

# Excel sheets
sheets = ["DFT_data", "XTB_data_noNi", "XTB_data_Ni"]
project_names = ["Kraken DFT", "Kraken XTB", "Kraken XTB_Ni"]

# User
user = User.objects.get(username='Kraken')

print("Got user.")

# Load data from Excel
excel_file_path = os.path.join(script_dir, 'descriptors.xlsx')
xl_file = pd.ExcelFile(excel_file_path)

# Set up logging
logging.basicConfig(filename='kraken_data_upload.log', level=logging.WARNING)
logging.info("Loaded Excel File. Starting Program...\n\n")

print("Loaded Excel File. Starting Program...\n\n")

for sheet, project_name in zip(sheets, project_names):
    df = xl_file.parse(sheet)

    for _, row in df.iterrows():
        # Database ID
        db_id = 'KRAKEN_{:08}'.format(row[0])
        logging.info(f"\n\n\n### MOVING TO: {db_id} ###\n\n\n")
        print(f"### MOVING TO: {db_id} ###")

        # Check and see if database_id exists or no
        try:
            conf_ensemble = ConformationalEnsemble.objects.get(database_id=db_id)

            # Check if a Statistics object already exists for this Conformational Ensemble
            statistics, created = Statistics.objects.get_or_create(user=user, conformational_ensemble=conf_ensemble)

            if created:
                logging.info(f"\n\nCreated new Statistics object for database_id {db_id}")
            else:
                logging.info(f"\n\nUsing existing Statistics object for database_id {db_id}")

            for col in df.columns[2:]:
                split_col = col.upper().split("_")
                group = split_col[0]
                cond_prop_key_name = split_col[-1]
                variant = "_".join(split_col[1:-1])

                logging.info(f"Group: {group}, Variant: {variant}, Project Name: {project_name}, Condensed Property Key: {cond_prop_key_name}")
                # Parameter Type
                param_type = ParameterType.objects.get(group=group, variant=variant, project_name=project_name)

                # Condensed Property Key
                cond_prop_key = CondensedPropertyKey.objects.get(name=cond_prop_key_name)

                # Value
                value = row[col]

                # Atoms referenced
                atoms_referenced = str([phosphorous_indices[db_id]])

                # Parameter
                param = Parameter(condensed_property_key=cond_prop_key, parameter_type=param_type, value=value, atoms_referenced=atoms_referenced)
                param.save()

                # Add Parameter to Statistics
                statistics.parameters.add(param)

        except ConformationalEnsemble.DoesNotExist:
            logging.warning(f"Warning: Conformational Ensemble with database_id {db_id} does not exist.")
            continue

        # Save Statistics
        statistics.save()
