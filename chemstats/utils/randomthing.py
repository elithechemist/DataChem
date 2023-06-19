import logging
import os
import sys
import django

# Add the parent directory to the Python path (update as necessary)
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_path)

# Set the Django settings module environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chemstats.settings")

# Initialize Django
django.setup()

from stats.models import ParameterType

# Set up logging
logging.basicConfig(filename='randomthing.txt', level=logging.INFO)
logging.info("Starting script...\n\n")

def update_objects():
    # Retrieve objects with project_name "Kraken XTB_Ni"
    original_objects = ParameterType.objects.all()

    # Update the num_atoms_required to 1 for each object
    for original_object in original_objects:
        original_object.num_atoms_required = 1
        original_object.save()

    # Logging
    logging.info(f"Updated {original_objects.count()} objects.")

# Call the function
update_objects()
