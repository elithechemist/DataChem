# Get_Properties_Notebook
Brittany C. Haas and Melissa A. Hardy's workflow scripts for automated collection of molecular descriptors and post-processing (i.e., Boltzmann average, min/max values, etc.). 

## Environment Setup
Uses Python/3.8.8
### One time setup instructions for Windows or Mac users: 
    Step 1: Create a conda environment using the correct .yml file for your operating system: 
      Windows: conda env create -f gpenv_win.yml
      Mac: conda env create -f gpenv_mac.yml
    Step 2: Activate it: 
      Windows: conda activate gpenv_win 
      Mac: conda activate gpenv_mac
    Step 3: Install Goodvibes (Jupyter Notebook branch) 
      git clone https://github.com/patonlab/goodvibes
      cd goodvibes
      git checkout GV2021
      python setup.py install 

Make sure the kernel is set to the correct environment when using Jupyter Notebook.

### One time setup instructions for Utah's CHPC: 
    See the CHPCenv_instructions document for how to setup the envrionment necessary to use the Get_Properties_Notebook on the CHPC.
    
## Properties
  * energies (goodvibes)
  * nbo 
  * nmr 
  * angle
  * dihedral angle
  * distance
  * plane angle
  * total time
  * frontier molecular orbitals
  * volume
  * polarizability
  * dipole
  * Sterimol (morfeus)
  * buried Sterimol (morfeus)
  * buried volume (morfeus)
  * buried volume scan (morfeus)
  * pyramidalization (morfeus)
  * solvent accessible surface area (SASA) & sphericity (morfeus)
  * Sterimol (dbstep)
  * Sterimol2Vec (dbstep)
  * Hirshfeld charges 
  * ChelpG
  * IR stretching frequency – *works for one stretch in the input range*
  * Consult Brittany or Melissa for: buried volume (hemispheres, quadrants, octants) and nborbs *(can be customized depending the types of orbital occupancy/energies you want out)*

Be sure to include correct Gaussian input lines for descriptors you will want (i.e., nbo, nmr, volume, etc.)

## Important Notes
  * This script assumes that you have conformational ensembles for multiple compounds and that your naming scheme has some prefix, compound identifier (i.e., number, letter, name), suffix, and conformer number (i.e., Ac1_1.log. Ac1_2.log. Ac2_1.log. Ac2_2.log).
    * If this is not the case, you can use a bulk renaming utility to adopt suitable names. 
      * For Windows users: Bulk Rename Utiliy 
      * For Mac and Windows users: Beck has a python script
  * This script is only intended to get properties for **linked** jobs.
    * If you don’t have linked jobs, get your own energies, read them in in the atom map Excel with an extra column for energy or add them to the manual_properties_sample.xlsx.
      * Cannot get Gibbs energy for a single point job with solvent model

## Acknowledgements
Portions are adapted from code by David B. Vogt and Jordan P. Liles.