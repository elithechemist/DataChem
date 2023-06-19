from openbabel import pybel
from openbabel import openbabel as ob
from django.conf import settings
from rdkit import Chem
import os, re
import boto3
from chemstats.utils.storage import s3_molecule_retrieve, s3_molecule_store


def g09_to_xyz(file_name):
    """
    Converts a GAUSSIAN-09 .LOG file to a .XYZ file and uploads it to the S3 temp folder.
    """
    log_file = s3_molecule_retrieve(file_name)

    # Generate the xyz file
    molecule = pybel.readstring('g09', log_file)
    file_name = file_name.split('.')[0] + '.xyz'
    s3_molecule_store(file_name, molecule.write('xyz'))

    return file_name

def xyz_to_smiles(file_name):
    # Generate the smiles
    xyz_file = s3_molecule_retrieve(file_name)
    molecule = pybel.readstring('xyz', xyz_file)
    smiles = molecule.write(format="smiles")
    print("SMILES: " + smiles)

    return(smiles)
