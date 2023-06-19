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

# Load the first Excel file
script_dir = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(script_dir, 'descriptors.xlsx')
data = pd.read_excel(excel_path)

# Load the second Excel file
kraken_cas_to_id_path = os.path.join(script_dir, 'kraken_CAS_to_ID.xlsx')
kraken_cas_to_id_data = pd.read_excel(kraken_cas_to_id_path)

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

print(kraken_cas_to_id_data.head())  # Print the first few rows of the DataFrame
print(kraken_cas_to_id_data['ID'])   # Print the values in the 'ID' column

ids_processed = []

# Iterate through each row in the Excel file
for index, row in data.iterrows():
    if(index != 244):
        continue
    
    # Extract the ID from the first Excel file and pad it with zeros
    ensemble_id = row['ID']
    print(f"On ensemble ID: {ensemble_id}")

    # Find the corresponding row in the second Excel file based on the ID
    corresponding_row = kraken_cas_to_id_data.loc[kraken_cas_to_id_data['ID'] == ensemble_id]

    # Check if a corresponding row was found
    if not corresponding_row.empty:
        # Extract the ligand name and CAS ID from the corresponding row
        informal_names = corresponding_row['ligand'].iloc[0]
        cas_ids = corresponding_row['CAS PR3'].iloc[0]

    else:
        # No corresponding row found for the ID in the second Excel file
        logging.error(f"No corresponding row found for ID {ensemble_id}")
        print(f"No corresponding row found for ID {ensemble_id}")

    # Create a ConformationalEnsemble object
    ensemble = ConformationalEnsemble()

    # Extract multiple ligand names into a JSON string
    json_informal_names = json.dumps([name.strip() for name in informal_names.split(", ")])
    json_cas_ids = json.dumps([cas_id.strip() for cas_id in cas_ids.split(", ")])

    if cas_ids == "not on scifinder":
        logging.error(f"CAS ID not found for ID {ensemble_id}")
        print(f"CAS ID not found for ID {ensemble_id}")
        json_cas_ids = ""

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

        # Generate the ligand name after ensemble is created
        if ensemble.molecule_name == "BLANK":
            logging.warning(f'Molecule name is BLANK for ID {ensemble_id}. Changing to {ensemble.cas_ids[0]}...')
            print(f'Molecule name is BLANK for ID {ensemble_id}. Changing to {ensemble.cas_ids[0]}...')
            if ensemble.informal_names:
                try:
                    informal_names_array = json.loads(ensemble.informal_names)
                    ensemble.molecule_name = informal_names_array[0]
                except json.JSONDecodeError:
                    logging.error(f'Error decoding cas_ids JSON for ID {ensemble_id}')
                    # Handle the error condition as needed
            else:
                ensemble.molecule_name = "!!! FIX ME !!!"  # Set to empty string if cas_ids is empty

        ensemble.save()

        # Add ensemble to the Kraken library (assuming ensemble has a foreign key to Molecule model)
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
