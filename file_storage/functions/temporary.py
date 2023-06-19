import os
from django.conf import settings

LOG_FILE_PATH = os.path.join(settings.MEDIA_ROOT, 'log_files')
XYZ_FILE_PATH = os.path.join(settings.MEDIA_ROOT, 'xyz_files')

def log_to_xyz(file_name):
    mol.write("xyz", os.path.join(XYZ_FILE_PATH, file_name))
    return(f'Sucess! Access at: { LOG_FILE_PATH }/{ file_name }.xyz')

# Pring the phrase "Hello"
