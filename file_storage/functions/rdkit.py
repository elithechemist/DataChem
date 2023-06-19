import uuid
import boto3
from rdkit import Chem
from rdkit.Chem import Draw, AllChem, rdDepictor
from django.conf import settings
from openbabel import openbabel as ob
import tempfile
from chemstats.utils.storage import s3_molecule_store
import os, io

# Initialize the S3 client
s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

def smiles_to_svg(smiles, molecule_id):
    print("IN SMILES TO SVG")
    # Give molecules a preferred geometry
    rdDepictor.SetPreferCoordGen(True)

    # Create svg file
    mol = Chem.MolFromSmiles(smiles)
    drawer = Draw.MolDraw2DSVG(600, 300)

    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    unique_id = str(uuid.uuid4())
    file_name = f'{unique_id}.svg'

    print("FILE NAME: " + file_name)

    # Upload to S3
    s3_molecule_store(file_name, svg)

    return file_name


def smiles_to_labeled_svg(smiles, molecule_id):
    # Give molecules a preferred geometry
    rdDepictor.SetPreferCoordGen(True)

    # S3 path and name
    s3_path = f'svg_files_labeled/{molecule_id}.svg'

    # Create svg file
    mol = Chem.MolFromSmiles(smiles)

    drawer = Draw.MolDraw2DSVG(600, 300)

    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()

    # Upload to S3
    s3.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_path, Body=svg)

    return s3_path


def xyz_to_indexed_svg(xyz_file):
    """
    Generates an SVG file with the 2D structure of the molecule and the atom index.
    Atom indices are obtained from the xyz file, which should be in XYZ format (plain text file with space-separated values).
    This should facilitate choosing the appropriate atoms for parameter extraction from the original Gaussian output file.
    
    Args:
        xyz_file (str): Path to the xyz file in the MEDIA_ROOT/xyz_files directory.
        
    Returns:
        str: Path to the SVG file. Also generates the SVG file in the MEDIA_ROOT/svg_files_labeled directory.
    """
    # Give molecules a preferred geometry
    rdDepictor.SetPreferCoordGen(True)

    # Generate the mol file using openbabel
    ob_mol = ob.OBMol()
    
    # Assuming xyz_file content is passed as string
    obConversion = ob.OBConversion()
    obConversion.SetInAndOutFormats('xyz', 'mol')
    obConversion.ReadString(ob_mol, xyz_file)

    mol_string = obConversion.WriteString(ob_mol)

    # Generate the mol object using rdkit
    mol = Chem.MolFromMolBlock(mol_string)

    # Generate the 2D structure
    AllChem.Compute2DCoords(mol)

    # Iterate over the atoms in the Mol object and get the atom index
    for atom in mol.GetAtoms():
        # Label the atom with its index using its symbol and index
        atom.SetProp('atomNote', str(atom.GetIdx() + 1))

    drawer = Draw.MolDraw2DSVG(600, 300)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()

    # S3 path for the file
    s3_path = 'temp/svg_files_labeled/INDEXED.svg'

    # Upload to S3
    s3.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_path, Body=svg)

    return s3_path

class MolFile:
    @staticmethod
    def smiles_to_2d_mol_file(smiles, molecule_id):
        # Convert SMILES to RDKit molecule object
        mol = Chem.MolFromSmiles(smiles)

        # Generate 2D coordinates
        AllChem.Compute2DCoords(mol)

        # Create an in-memory text stream
        text_stream = io.StringIO()

        # Write Mol block to the in-memory text stream
        text_stream.write(Chem.MolToMolBlock(mol))
        text_stream.seek(0)  # Reset the stream position to the beginning

        file_name = f'{molecule_id}.mol'
        s3_molecule_store(file_name,  text_stream.read().encode())

        return file_name

    @staticmethod
    def extract_atom_indices(mol_file_s3_key, atomic_symbol):

        # Retrieve the file from S3 to an in-memory bytes stream
        mol_file_stream = io.BytesIO()
        mol_file_stream.seek(0)  # Reset the stream position to the beginning

        # Load the molecule from the in-memory bytes stream
        mol = Chem.MolFromMolBlock(mol_file_stream.read().decode())

        # Loop through atoms and find the indices with the matching atomic symbol
        indices = [atom.GetIdx() for atom in mol.GetAtoms() if atom.GetSymbol() == atomic_symbol]

        return indices
