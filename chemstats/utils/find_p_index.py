import os
import sys
import django
from rdkit import Chem
import json
from io import BytesIO

# Dynamically add the project to the Python path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(base_dir)
sys.path.append(project_dir)

# Set the Django settings module environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chemstats.settings") # Note the change here

# Initialize Django
django.setup()

# Now you can import other modules that depend on Django settings
from storage import s3_molecule_retrieve
import json
from io import BytesIO
from rdkit import Chem
from file_storage.models import ConformationalEnsemble

print("Django initialized. Starting script...\n\n")

# Function to find the index of the phosphorous atom
def find_phosphorous_index(file_content):
    # Read the MOL file from content
    mol = Chem.MolFromMolBlock(file_content)
    
    # Find the index of phosphorous atoms
    phosphorous_indices = [atom.GetIdx() for atom in mol.GetAtoms() if atom.GetSymbol() == 'P']
    
    # Check the number of phosphorous atoms
    if len(phosphorous_indices) > 1:
        print(f"Warning: More than one phosphorous atom found.")
        return None
    elif len(phosphorous_indices) == 0:
        print(f"No phosphorous atoms found.")
        return None
    else:
        # Return the index of the single phosphorous atom
        return phosphorous_indices[0]

# Dictionary to hold the database_id as key and index of the phosphorous as value
database_info = {}

# Iterate through all instances of ConformationalEnsemble
for ensemble in ConformationalEnsemble.objects.all():
    # Retrieve the file name
    file_name = ensemble.mol_file.name
    
    # Retrieve the file content from S3 using the provided function
    file_content = s3_molecule_retrieve(file_name, as_path=False)
    
    # Get the phosphorous index
    phosphorous_index = find_phosphorous_index(file_content)
    
    # Store in the dictionary
    database_info[ensemble.database_id] = phosphorous_index

# Write the information to a JSON file
with open('phosphorous_indices.json', 'w') as json_file:
    json.dump(database_info, json_file)
