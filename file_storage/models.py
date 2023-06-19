import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from file_storage.functions.rdkit import smiles_to_svg, MolFile
from file_storage.functions.openbabel import g09_to_xyz, xyz_to_smiles
from file_storage.functions.pubchem import smiles_to_iupac
import json, re
from django.core.files import File
from chemstats.utils.storage import s3_molecule_delete, s3_molecule_retrieve, s3_molecule_store

def get_computational_methods(logfile):
    print("LOG FILE: " + str(logfile))
    
    # Retrieve file, you might need to adapt this part
    file_content = s3_molecule_retrieve(logfile)
    
    # Join the content into a single string for regex matching
    file_content = ''.join(file_content)
    
    # Regular expression pattern
    pattern = re.compile(r'-{67}\s*\n\s*#\s(.*?)\s*-{67}', re.DOTALL)
    
    # Find all matches
    matches = pattern.findall(file_content)
    
    # Normalize the matches
    computational_methods = [' '.join(match.split()).upper() for match in matches]
    
    print("Computational Method: " + str(computational_methods))
    return computational_methods

class Library(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    conformational_ensembles = models.ManyToManyField('ConformationalEnsemble', blank=True)

class Molecule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    smiles = models.CharField(max_length=500, blank=True)
    log_file = models.FileField(upload_to='log_files', blank=True)
    ComputationalMethods = models.CharField(max_length=2000, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Save molecule so the file can be opened
        super(Molecule, self).save(*args, **kwargs)
        
        # Convert log file to xyz file and then to smiles
        g09_to_xyz(str(self.log_file))
        temp_xyz_file = str(self.log_file).split('.')[0] + '.xyz'
        smiles = xyz_to_smiles(temp_xyz_file)

        # Get computational methods
        computational_methods = get_computational_methods(str(self.log_file))
        computational_methods_json = json.dumps(computational_methods)
        self.ComputationalMethods = computational_methods_json
        print("Computational Method: " + str(computational_methods))
        self.smiles = smiles

        # Check if the computational method already exists
        computational_method, created = ComputationalMethod.objects.get_or_create(method=computational_methods[-1])

        # Check for existing ConformationalEnsemble with the same smiles key and user
        ensemble, created = ConformationalEnsemble.objects.get_or_create(user=self.user, smiles=self.smiles, computational_method=computational_method)
        
        if created:
            # Convert smiles to iupac name
            iupac = smiles_to_iupac(smiles)
            ensemble.molecule_name = iupac

            # Convert smiles to svg
            svg = smiles_to_svg(smiles, self.pk)
            print("SVG: " + str(svg))
            ensemble.svg_file = svg

            print("SAVING ENSEMBLE")
            ensemble.save()

        # Add this molecule to the ensemble
        ensemble.conformers.add(self)

        # Save molecule second time to update the smiles field
        super(Molecule, self).save(update_fields=['smiles', 'ComputationalMethods'])

    def delete(self, *args, **kwargs):
        ensembles = self.conformationalensemble_set.all()
        super().delete(*args, **kwargs)  # delete the Molecule first
        for ensemble in ensembles:
            if ensemble.conformers.count() == 0:  # check if there are no Molecules left
                ensemble.delete()  # delete the ConformationalEnsemble if it's empty

    def __str__(self):
        return f'{self.id}'  # Changed to id since molecule_name is removed


class ConformationalEnsemble(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    smiles = models.CharField(max_length=500, blank=True)
    cas_ids = models.TextField(blank=True)
    molecule_name = models.CharField(max_length=500, blank=True)
    informal_names = models.TextField
    database_id = models.CharField(max_length=500, blank=True)
    svg_file = models.FileField(upload_to='svg_files', blank=True)
    mol_file = models.FileField(upload_to='mol_files', blank=True)
    computational_method = models.ManyToManyField('ComputationalMethod', blank=True)
    conformers = models.ManyToManyField(Molecule, blank=True)

    def save(self, *args, **kwargs):
        unique_id = str(uuid.uuid4())
        print("UNIQUE ID: " + unique_id)
        
        # Generate and save Molecule name if not provided
        if not self.molecule_name:
            # If an IUPAC name is not fount, the SMILES string is used as a placeholder
            self.molecule_name = smiles_to_iupac(self.smiles)
        
        # Generate and save SVG if not provided
        if not self.svg_file:
            print("SVG FILE NOT PROVIDED")
            svg_file = smiles_to_svg(self.smiles, unique_id)
            self.svg_file = svg_file
        
        # Generate and save Mol file if not provided
        if not self.mol_file:
            mol_file = MolFile.smiles_to_2d_mol_file(self.smiles, svg_file.strip('.svg'))
            self.mol_file = mol_file
        
        # Call the parent class's save() method
        super(ConformationalEnsemble, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the files from S3
        if self.mol_file:
            s3_molecule_delete(self.mol_file.name)
        
        if self.svg_file:
            s3_molecule_delete(self.svg_file.name)
        
        # Call the parent class's delete() method
        super(ConformationalEnsemble, self).delete(*args, **kwargs)

    def __str__(self):
        return f'{self.database_id}'
    
class ComputationalMethod(models.Model):
    method = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return f'{self.method}'
    
class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    conformational_ensembles = models.ManyToManyField(ConformationalEnsemble)
    name = models.CharField(max_length=500, blank=True)

class ParameterType(models.Model):
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=500, blank=True)
    num_indices = models.IntegerField(default=0)

class EnsembleParameter(models.Model):
    conformational_ensemble = models.ForeignKey(ConformationalEnsemble, on_delete=models.CASCADE)
    parameter_type = models.ForeignKey(ParameterType, on_delete=models.CASCADE)
    indices = models.JSONField(blank=True, null=True)  # Store indices as JSON
    value = models.FloatField()