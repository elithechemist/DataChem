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

# Add this list of substrate IDs that you want to process
substrate_ids_to_process = {'KRAKEN_00000096', 'KRAKEN_00000097', 'KRAKEN_00000098', 'KRAKEN_00000112', 'KRAKEN_00000270', 
                            'KRAKEN_00000283', 'KRAKEN_00000359', 'KRAKEN_00000360', 'KRAKEN_00000361', 'KRAKEN_00000362', 
                            'KRAKEN_00000367', 'KRAKEN_00000419', 'KRAKEN_00000420', 'KRAKEN_00000421', 'KRAKEN_00000422', 
                            'KRAKEN_00000526', 'KRAKEN_00000546', 'KRAKEN_00000571', 'KRAKEN_00000572', 'KRAKEN_00000573', 
                            'KRAKEN_00000585', 'KRAKEN_00000592', 'KRAKEN_00000593', 'KRAKEN_00000596', 'KRAKEN_00000597', 
                            'KRAKEN_00000599', 'KRAKEN_00000601', 'KRAKEN_00000603', 'KRAKEN_00000605', 'KRAKEN_00000613', 
                            'KRAKEN_00000616', 'KRAKEN_00000619', 'KRAKEN_00000620', 'KRAKEN_00000621', 'KRAKEN_00000624', 
                            'KRAKEN_00000626', 'KRAKEN_00000627', 'KRAKEN_00000628', 'KRAKEN_00000629', 'KRAKEN_00000630', 
                            'KRAKEN_00000631', 'KRAKEN_00000632', 'KRAKEN_00000633', 'KRAKEN_00000634', 'KRAKEN_00000635', 
                            'KRAKEN_00000636', 'KRAKEN_00000637', 'KRAKEN_00000711', 'KRAKEN_00000713', 'KRAKEN_00000719', 
                            'KRAKEN_00000724', 'KRAKEN_00000742', 'KRAKEN_00000743', 'KRAKEN_00000786', 'KRAKEN_00000787', 
                            'KRAKEN_00000788', 'KRAKEN_00000789', 'KRAKEN_00000801', 'KRAKEN_00000802', 'KRAKEN_00000803', 
                            'KRAKEN_00000804', 'KRAKEN_00000805', 'KRAKEN_00000806', 'KRAKEN_00000807', 'KRAKEN_00000808', 
                            'KRAKEN_00000809', 'KRAKEN_00000810', 'KRAKEN_00000811', 'KRAKEN_00000812', 'KRAKEN_00000813', 
                            'KRAKEN_00000814', 'KRAKEN_00000815', 'KRAKEN_00000816', 'KRAKEN_00000817', 'KRAKEN_00000818', 
                            'KRAKEN_00000819', 'KRAKEN_00000822', 'KRAKEN_00000823', 'KRAKEN_00000824', 'KRAKEN_00000825', 
                            'KRAKEN_00000826', 'KRAKEN_00000827', 'KRAKEN_00000828', 'KRAKEN_00000829', 'KRAKEN_00000834', 
                            'KRAKEN_00000841', 'KRAKEN_00000842', 'KRAKEN_00000843', 'KRAKEN_00000844', 'KRAKEN_00000845', 
                            'KRAKEN_00000846', 'KRAKEN_00000847', 'KRAKEN_00000849', 'KRAKEN_00000850', 'KRAKEN_00000854', 
                            'KRAKEN_00000855', 'KRAKEN_00000856', 'KRAKEN_00000857', 'KRAKEN_00000858', 'KRAKEN_00000859', 
                            'KRAKEN_00000860', 'KRAKEN_00000861', 'KRAKEN_00000863', 'KRAKEN_00000868', 'KRAKEN_00000869', 
                            'KRAKEN_00000890', 'KRAKEN_00000895', 'KRAKEN_00000900', 'KRAKEN_00000901', 'KRAKEN_00000903', 
                            'KRAKEN_00000904', 'KRAKEN_00000905', 'KRAKEN_00000906', 'KRAKEN_00000907', 'KRAKEN_00000914', 
                            'KRAKEN_00000932', 'KRAKEN_00000938', 'KRAKEN_00000939', 'KRAKEN_00000940', 'KRAKEN_00000941', 
                            'KRAKEN_00000942', 'KRAKEN_00000943', 'KRAKEN_00000944', 'KRAKEN_00000946', 'KRAKEN_00000947', 
                            'KRAKEN_00000948', 'KRAKEN_00000954', 'KRAKEN_00000968', 'KRAKEN_00000969', 'KRAKEN_00000971', 
                            'KRAKEN_00000975', 'KRAKEN_00000979', 'KRAKEN_00001010', 'KRAKEN_00001014', 'KRAKEN_00001030', 
                            'KRAKEN_00001057', 'KRAKEN_00001058', 'KRAKEN_00001062', 'KRAKEN_00001077', 'KRAKEN_00001078', 
                            'KRAKEN_00001079', 'KRAKEN_00001080', 'KRAKEN_00001081', 'KRAKEN_00001082', 'KRAKEN_00001116', 
                            'KRAKEN_00001117', 'KRAKEN_00001120', 'KRAKEN_00001123', 'KRAKEN_00001124', 'KRAKEN_00001125', 
                            'KRAKEN_00001126', 'KRAKEN_00001133', 'KRAKEN_00001134', 'KRAKEN_00001135', 'KRAKEN_00001175', 
                            'KRAKEN_00001191', 'KRAKEN_00001192', 'KRAKEN_00001193', 'KRAKEN_00001194', 'KRAKEN_00001195', 
                            'KRAKEN_00001200', 'KRAKEN_00001213', 'KRAKEN_00001240', 'KRAKEN_00001248', 'KRAKEN_00001276', 
                            'KRAKEN_00001300', 'KRAKEN_00001301', 'KRAKEN_00001302', 'KRAKEN_00001303', 'KRAKEN_00001304', 
                            'KRAKEN_00001305', 'KRAKEN_00001306', 'KRAKEN_00001307', 'KRAKEN_00001308', 'KRAKEN_00001309', 
                            'KRAKEN_00001310', 'KRAKEN_00001311', 'KRAKEN_00001312', 'KRAKEN_00001313', 'KRAKEN_00001314', 
                            'KRAKEN_00001315', 'KRAKEN_00001316', 'KRAKEN_00001317', 'KRAKEN_00001318', 'KRAKEN_00001319', 
                            'KRAKEN_00001320', 'KRAKEN_00001321', 'KRAKEN_00001322', 'KRAKEN_00001323', 'KRAKEN_00001324', 
                            'KRAKEN_00001325', 'KRAKEN_00001326', 'KRAKEN_00001327', 'KRAKEN_00001328', 'KRAKEN_00001329', 
                            'KRAKEN_00001330', 'KRAKEN_00001331', 'KRAKEN_00001332', 'KRAKEN_00001333', 'KRAKEN_00001334', 
                            'KRAKEN_00001335', 'KRAKEN_00001336', 'KRAKEN_00001337', 'KRAKEN_00001338', 'KRAKEN_00001339', 
                            'KRAKEN_00001340', 'KRAKEN_00001341', 'KRAKEN_00001342', 'KRAKEN_00001343', 'KRAKEN_00001344', 
                            'KRAKEN_00001345', 'KRAKEN_00001346', 'KRAKEN_00001347', 'KRAKEN_00001348', 'KRAKEN_00001349', 
                            'KRAKEN_00001350', 'KRAKEN_00001351', 'KRAKEN_00001352', 'KRAKEN_00001353', 'KRAKEN_00001354', 
                            'KRAKEN_00001355', 'KRAKEN_00001356', 'KRAKEN_00001357', 'KRAKEN_00001358', 'KRAKEN_00001359', 
                            'KRAKEN_00001360', 'KRAKEN_00001361', 'KRAKEN_00001362', 'KRAKEN_00001363', 'KRAKEN_00001364', 
                            'KRAKEN_00001365', 'KRAKEN_00001366', 'KRAKEN_00001367', 'KRAKEN_00001368', 'KRAKEN_00001369', 
                            'KRAKEN_00001370', 'KRAKEN_00001371', 'KRAKEN_00001372', 'KRAKEN_00001373', 'KRAKEN_00001374', 
                            'KRAKEN_00001375', 'KRAKEN_00001376', 'KRAKEN_00001377', 'KRAKEN_00001378', 'KRAKEN_00001379', 
                            'KRAKEN_00001380', 'KRAKEN_00001381', 'KRAKEN_00001382', 'KRAKEN_00001383', 'KRAKEN_00001384', 
                            'KRAKEN_00001385', 'KRAKEN_00001386', 'KRAKEN_00001387', 'KRAKEN_00001388', 'KRAKEN_00001389', 
                            'KRAKEN_00001390', 'KRAKEN_00001391', 'KRAKEN_00001392', 'KRAKEN_00001393', 'KRAKEN_00001394', 
                            'KRAKEN_00001395', 'KRAKEN_00001396', 'KRAKEN_00001397', 'KRAKEN_00001398', 'KRAKEN_00001399', 
                            'KRAKEN_00001411', 'KRAKEN_00001416', 'KRAKEN_00001421', 'KRAKEN_00001424', 'KRAKEN_00001426', 
                            'KRAKEN_00001427', 'KRAKEN_00001429', 'KRAKEN_00001431', 'KRAKEN_00001432', 'KRAKEN_00001442', 
                            'KRAKEN_00001443', 'KRAKEN_00001445', 'KRAKEN_00001446', 'KRAKEN_00001452', 'KRAKEN_00001464', 
                            'KRAKEN_00001465', 'KRAKEN_00001466', 'KRAKEN_00001467', 'KRAKEN_00001471', 'KRAKEN_00001472', 
                            'KRAKEN_00001473', 'KRAKEN_00001474', 'KRAKEN_00001483', 'KRAKEN_00001484', 'KRAKEN_00001489', 
                            'KRAKEN_00001511', 'KRAKEN_00001512', 'KRAKEN_00001513', 'KRAKEN_00001514', 'KRAKEN_00001515', 
                            'KRAKEN_00001516'}

# Iterate through each row in the Excel file
for index, row in data.iterrows():
    # Extract the ID from the first Excel file and pad it with zeros
    ensemble_id = row['ID']

    # Convert ensemble_id to the format with KRAKEN_ prefix and zeros
    formatted_ensemble_id = f"KRAKEN_{str(ensemble_id).zfill(8)}"

    # Only process IDs that are in substrate_ids_to_process
    if formatted_ensemble_id in substrate_ids_to_process:
        try:
            print(f"On ensemble ID: {formatted_ensemble_id}")

            # Create a ConformationalEnsemble object
            ensemble = ConformationalEnsemble()

            # Set cas_ids and informal_names to blank
            json_cas_ids = ""
            json_informal_names = ""

            logging.info(f"Processing ensemble {formatted_ensemble_id}...")

            # Assign values to fields
            ensemble.user = user
            ensemble.smiles = row['smiles']
            ensemble.database_id = formatted_ensemble_id
            ensemble.cas_ids = json_cas_ids
            ensemble.informal_names = json_informal_names

            # Attempt to save the object, log an error if it fails or takes too long
            start_time = time.time()
            ensemble.save()

            # Associate the computational methods
            ensemble.computational_method.add(xtb, dft)

            # Generate the ligand name after ensemble is created
            if ensemble.molecule_name == "BLANK":
                logging.warning(f'Molecule name is BLANK for ID {formatted_ensemble_id}. Changing to {ensemble.cas_ids[0]}...')
                print(f'Molecule name is BLANK for ID {formatted_ensemble_id}. Changing to {ensemble.cas_ids[0]}...')
                ensemble.molecule_name = ensemble.smiles if not ensemble.informal_names else ensemble.informal_names[0]

            ensemble.save()

            # Add ensemble to the Kraken library
            kraken_library.conformational_ensembles.add(ensemble)
            end_time = time.time()

            # If saving took longer than 60 seconds, log it
            if end_time - start_time > 60:
                logging.error(f"Row {index + 1} took longer than 60 seconds to process")

            logging.info(f"\n\nPROCESSED ENSEMBLE: {formatted_ensemble_id}\n\n")

        except Exception as e:
            # Log the error and continue to the next row
            logging.error(f"Error processing ensemble ID {formatted_ensemble_id}: {str(e)}")
            print(f"ERROR: Ensemble ID {formatted_ensemble_id} was NOT processed!")

# Indicate that the script finished processing
print("Finished processing")
logging.info("Finished processing")
