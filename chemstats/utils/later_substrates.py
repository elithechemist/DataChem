import os
import sys
import django
import logging
import time
import pandas as pd
import json

# Add the parent directory of `chemstats` to the Python path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_path)

# Set the Django settings module environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chemstats.settings")

# Initialize Django
django.setup()

from file_storage.models import ConformationalEnsemble, ComputationalMethod, Library
from django.contrib.auth.models import User

# Set up logging
logging.basicConfig(filename='logger.txt', level=logging.INFO)
logging.info("Starting script...\n\n")

# Load the Excel file
script_dir = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(script_dir, 'descriptors.xlsx')
data = pd.read_excel(excel_path)

# Specify the username of the user you want to associate with the entries
username = 'Kraken'

# Fetch the user by username
try:
    user = User.objects.get(username=username)
except User.DoesNotExist:
    logging.error(f"User with username {username} does not exist.")
    exit()

# Get or create the computational methods
xtb, created = ComputationalMethod.objects.get_or_create(method="XTB")
dft, created = ComputationalMethod.objects.get_or_create(method="DFT")

# Get or create the Library named "Kraken"
kraken_library, created = Library.objects.get_or_create(name="Kraken", user=user)

ids_processed = []

# Iterate through each row in the Excel file
for index, row in data.iterrows():
    # Extract the ID from the first Excel file and pad it with zeros
    ensemble_id = row['ID']

    # Only process IDs from 1518 to 2000
    if 1518 <= ensemble_id <= 2000:
        print(f"On ensemble ID: {ensemble_id}")

        # Create a ConformationalEnsemble object
        ensemble = ConformationalEnsemble()

        # Set cas_ids and informal_names to blank
        json_cas_ids = ""
        json_informal_names = ""

        # Fill ensemble ID with zeros
        ensemble_id = str(ensemble_id).zfill(8)

        logging.info(f"Processing ensemble {ensemble_id}...")

        # Assign values to fields
        ensemble.user = user
        ensemble.smiles = row['smiles']
        ensemble.database_id = f"KRAKEN_{ensemble_id}"
        ensemble.cas_ids = json_cas_ids
        ensemble.informal_names = json_informal_names

        # Attempt to save the object, log an error if it fails or takes too long
        try:
            start_time = time.time()
            ensemble.save()

            # Associate the computational methods
            ensemble.computational_method.add(xtb, dft)

            # If the molecule_name is "BLANK", replace it with the SMILES string
            if ensemble.molecule_name == "BLANK":
                logging.warning(f'Molecule name is BLANK for ID {ensemble_id}. Changing to SMILES string...')
                print(f'Molecule name is BLANK for ID {ensemble_id}. Changing to SMILES string...')
                ensemble.molecule_name = ensemble.smiles

            ensemble.save()

            # Add ensemble to the Kraken library
            kraken_library.conformational_ensembles.add(ensemble)
            end_time = time.time()

            # If saving took longer than 60 seconds, log it
            if end_time - start_time > 60:
                logging.error(f"Row {index + 1} took longer than 60 seconds to process")

            logging.info(f"\n\nPROCESSED ENSEMBLE: {ensemble_id}\n\n")
            ids_processed.append(ensemble_id)

        except Exception as e:
            # Log the error and continue to the next row
            logging.error(f"Error processing row {index + 1}: {str(e)}")
            continue

# Indicate that the script finished processing
print("Finished processing")
logging.info("Finished processing")
print(f"Processed {len(ids_processed)} ensembles: {ids_processed}")
logging.info(f"Processed {len(ids_processed)} ensembles: {ids_processed}")
