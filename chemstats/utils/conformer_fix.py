import os
import sys
import django
import logging
import json

# Add the parent directory to the Python path (update as necessary)
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_path)

# Set the Django settings module environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chemstats.settings")

# Initialize Django
django.setup()

from file_storage.models import ConformationalEnsemble

# Set up logging
logging.basicConfig(filename='logger.txt', level=logging.INFO)
logging.info("Starting script...\n\n")

# Keeping track of missing IDs
missing_ids = []

# Iterate through the range of numbers
for number in range(1, 2001):  # 2001 to include KRAKEN_00002000
    formatted_id = f"KRAKEN_{str(number).zfill(8)}"

    # Fetch ConformationalEnsemble by database_id
    try:
        ensemble = ConformationalEnsemble.objects.get(database_id=formatted_id)
    except ConformationalEnsemble.DoesNotExist:
        logging.info(f"Missing ID: {formatted_id}")
        logging.info(f"Skipping {formatted_id}")
        missing_ids.append(formatted_id)
        continue
    except ConformationalEnsemble.MultipleObjectsReturned:
        logging.error(f"Multiple objects found for ID: {formatted_id}. Skipping this ID.")
        continue

    # Check if the molecule_name is "BLANK"
    if ensemble.molecule_name == "BLANK":
        # Check if informal_names is not empty and make the change
        if ensemble.informal_names:
            try:
                informal_names_array = json.loads(ensemble.informal_names)
                if informal_names_array:
                    ensemble.molecule_name = informal_names_array[0]
                    ensemble.save()
                    logging.info(f"Updated molecule_name for {formatted_id} to {informal_names_array[0]}")
                    print(f"Updated molecule_name for {formatted_id} to {informal_names_array[0]}")
            except json.JSONDecodeError:
                logging.error(f"Error decoding informal_names JSON for {formatted_id}")

# Log the missing IDs
logging.info(f"Missing IDs: {missing_ids}")
print(f"Missing IDs: {missing_ids}")

# Indicate that the script finished processing
print("Finished processing")
logging.info("Finished processing")
