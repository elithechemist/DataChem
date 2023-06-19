import tempfile
from django import forms
from .models import Molecule, Project
from .functions import get_properties
import re, os
from django.conf import settings
import boto3

class MoleculeForm(forms.ModelForm):
    log_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = Molecule
        fields = ['log_file']

class ParameterForm(forms.Form):
    s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    
    # List files from the S3 bucket
    prefix = f"media/log_files/"
    response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix)
    s3_objects = response.get('Contents', [])
    log_files = [(obj['Key'], obj['Key'].split('/')[-1]) for obj in s3_objects if obj['Key'].endswith('.log')]
    
    log_file = forms.ChoiceField(choices=log_files, label='Log File', required=True)
    method = forms.BooleanField(label='Method', required=False)
    e_boolean = forms.BooleanField(label='Energy', required=False)
    homo_boolean = forms.BooleanField(label='HOMO Energy', required=False)
    lumo_boolean = forms.BooleanField(label='LUMO Energy', required=False)
    nbo_boolean = forms.BooleanField(label='NBO Charge', required=False)
    nbo_atom = forms.IntegerField(label='NBO Atom', required=False)
    dihedral_boolean = forms.BooleanField(label='Dihedral Angle', required=False)
    dihedral_atom1 = forms.IntegerField(label='Dihedral Atom 1', required=False)
    dihedral_atom2 = forms.IntegerField(label='Dihedral Atom 2', required=False)
    dihedral_atom3 = forms.IntegerField(label='Dihedral Atom 3', required=False)
    dihedral_atom4 = forms.IntegerField(label='Dihedral Atom 4', required=False)
    angle_boolean = forms.BooleanField(label='Angle', required=False)
    angle_atom1 = forms.IntegerField(label='Angle Atom 1', required=False)
    angle_atom2 = forms.IntegerField(label='Angle Atom 2', required=False)
    angle_atom3 = forms.IntegerField(label='Angle Atom 3', required=False)
    dist_boolean = forms.BooleanField(label='Bond Distance', required=False)
    dist_atom1 = forms.IntegerField(label='Distance Atom 1', required=False)
    dist_atom2 = forms.IntegerField(label='Distance Atom 2', required=False)

    def clean(self):
        cleaned_data = super().clean()

        log_file_s3_key = cleaned_data.get('log_file')

        # Download the file from S3 to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".log") as temp_file:
            self.s3_client.download_file(settings.AWS_STORAGE_BUCKET_NAME, log_file_s3_key, temp_file.name)
            molecule_path = temp_file.name

        # Process any calculations or validations you need
        if cleaned_data.get('method'):
            last_num = get_properties.main(['X'], "0", molecule_path)[1]
            method = last_num
        else:
            method = None
        
        if cleaned_data.get('e_boolean'):
            last_num = get_properties.main(['e'], "0", molecule_path)[1].split(";")[-2]
            e = last_num
        else:
            e = None

        if cleaned_data.get('homo_boolean'):
            first_num = get_properties.main(['homo'], "0", molecule_path)[1].split(";")[0]
            homo = first_num
        else:
            homo = None

        if cleaned_data.get('lumo_boolean'):
            second_num = get_properties.main(['homo'], "0", molecule_path)[1].split(";")[1]
            lumo = second_num
        else:
            lumo = None

        if cleaned_data.get('nbo_boolean'):
            atom1 = str(cleaned_data.get('nbo_atom'))
            last_num = get_properties.main(['nbo'], [atom1], molecule_path)[1].split(";")[-2]
            nbo = last_num
            nbo_atom = atom1
        else:
            nbo = None
            nbo_atom = None

        if cleaned_data.get('dihedral_boolean'):
            dihedral_atom1 = str(cleaned_data.get('dihedral_atom1'))
            dihedral_atom2 = str(cleaned_data.get('dihedral_atom2'))
            dihedral_atom3 = str(cleaned_data.get('dihedral_atom3'))
            dihedral_atom4 = str(cleaned_data.get('dihedral_atom4'))
            last_num = get_properties.main(['dihedral'], [dihedral_atom1, dihedral_atom2, dihedral_atom3, dihedral_atom4], molecule_path)[1].split(";")[-2]
            dihedral = last_num
        else:
            dihedral = None
            dihedral_atom1 = None
            dihedral_atom2 = None
            dihedral_atom3 = None
            dihedral_atom4 = None

        if cleaned_data.get('angle_boolean'):
            angle_atom1 = str(cleaned_data.get('angle_atom1'))
            angle_atom2 = str(cleaned_data.get('angle_atom2'))
            angle_atom3 = str(cleaned_data.get('angle_atom3'))
            last_num = get_properties.main(['angle'], [angle_atom1, angle_atom2, angle_atom3], molecule_path)[1].split(";")[-2]
            angle = last_num
        else:
            angle = None
            angle_atom1 = None
            angle_atom2 = None
            angle_atom3 = None

        if cleaned_data.get('dist_boolean'):
            dist_atom1 = str(cleaned_data.get('dist_atom1'))
            dist_atom2 = str(cleaned_data.get('dist_atom2'))
            last_num = get_properties.main(['dist'], [dist_atom1, dist_atom2], molecule_path)[1].split(";")[-2]
            dist = last_num
        else:
            dist = None
            dist_atom1 = None
            dist_atom2 = None

        cleaned_data = {}
        cleaned_data['log_file'] = self.cleaned_data.get('log_file')
        cleaned_data['method'] = method
        cleaned_data['e'] = e
        cleaned_data['homo'] = homo
        cleaned_data['lumo'] = lumo
        cleaned_data['nbo'] = nbo
        cleaned_data['nbo_atom'] = nbo_atom
        cleaned_data['dihedral'] = dihedral
        cleaned_data['dihedral_atom1'] = dihedral_atom1
        cleaned_data['dihedral_atom2'] = dihedral_atom2
        cleaned_data['dihedral_atom3'] = dihedral_atom3
        cleaned_data['dihedral_atom4'] = dihedral_atom4
        cleaned_data['angle'] = angle
        cleaned_data['angle_atom1'] = angle_atom1
        cleaned_data['angle_atom2'] = angle_atom2
        cleaned_data['angle_atom3'] = angle_atom3
        cleaned_data['dist'] = dist
        cleaned_data['dist_atom1'] = dist_atom1
        cleaned_data['dist_atom2'] = dist_atom2

        return cleaned_data
    
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name']