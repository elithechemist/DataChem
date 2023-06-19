import os,re,sys,pickle,datetime,time,random,itertools,glob
from itertools import permutations
import warnings
warnings.filterwarnings("ignore")
import numpy as np
np.set_printoptions(threshold=sys.maxsize) #print out full arrays
import openpyxl
from openpyxl import load_workbook
import pandas as pd
from pandas import ExcelWriter
import xlsxwriter

import math
randomstate = 42

from rdkit import Chem

from goodvibes import GoodVibes as gv
from goodvibes import thermo as thermo
from goodvibes import io as io
from goodvibes import pes as pes
from morfeus import ConeAngle
from morfeus import Sterimol
import get_properties_functions as gp

def extract_parameters(log_files_folder, sdf_file, smarts_string, *args, **kwargs):
    substructure = Chem.MolFromSmarts(smarts_string)

    #generate a list of molecules using RDkit
    all_compounds = Chem.SDMolSupplier(sdf_file, removeHs=False)

    #uses RDKit to search for the substructure in each compound you will analyze
    atoms = []
    for molecule in all_compounds:
        if molecule is not None:
            submatch = molecule.GetSubstructMatches(substructure) #find substructure
            matchlist = list([item for sublist in submatch for item in sublist]) #list of zero-indexed atom numbers
            match_idx = [x+1 for x in matchlist] #this line changes from 0-indexed to 1-indexed (for Gaussian)
            atoms.append(match_idx) #append 1-indexed list to atoms (a list of lists)
            
    #this loop extracts log names from log_ids and splits them to the desired format
    list_of_filenames = os.listdir(log_files_folder)
    list_of_files = []
    for filename in list_of_filenames:
        file = filename[0].split(".")
        list_of_files.append(file[0])

    #put the atom numbers for the substructure for each log file into a dataframe
    prelim_df = pd.DataFrame(atoms)
    index=list_of_files
    prelim_df.insert(0,column='log_name',value=list_of_files)

    atom_labels = {'log_name': 'log_name',
                0: 'C4',
                1: 'C1', 
                2: 'O3',
                3: 'H5',
                4: 'O2'}
    
    #rename columns using the user input above
    atom_map_df = prelim_df.rename(columns=atom_labels)
    print(atom_map_df)

    #you can use this to clean up the table if you have more atoms in your substructure than you want to collect descriptors for
    #atom_map_df = atom_map_df.drop(columns= ['C4', 'C1']) 
    #display(atom_map_df.head())

    df = atom_map_df #df is what properties will be appended to, this creates a copy so that you have the original preserved 
    print(df)

    ################################################ Properties ################################################

    #---------------GoodVibes Energies---------------
    #uses the GoodVibes 2021 Branch (Jupyter Notebook Compatible)
    #calculates the quasi harmonic corrected G(T) and single point corrected G(T) as well as other thermodynamic properties
    #inputs: dataframe, temperature
    df = gp.get_goodvibes_e(df, 298.15)

    #---------------Frontier Orbitals-----------------
    #E(HOMO), E(LUMO), mu(chemical potential or negative of molecular electronegativity), eta(hardness/softness), omega(electrophilicity index)
    df = gp.get_frontierorbs(df)

    #---------------Polarizability--------------------
    #Exact polarizability
    df = gp.get_polarizability(df)

    #---------------Dipole----------------------------
    #Total dipole moment magnitude in Debye
    df = gp.get_dipole(df)

    #---------------Volume----------------------------
    #Molar volume
    #requires the Gaussian keyword = "volume" in the .com file
    df = gp.get_volume(df)

    #---------------SASA------------------------------
    #Uses morfeus to calculat sovlent accessible surface area and the volume under the SASA
    df = gp.get_SASA(df)

    #---------------NBO-------------------------------
    #natural charge from NBO
    #requires the Gaussian keyword = "pop=nbo7" in the .com file
    nbo_list = ["C1", "O2", "O3", "C4"]
    df = gp.get_nbo(df, nbo_list) 

    #---------------NMR-------------------------------
    #isotropic NMR shift
    #requires the Gaussian keyword = "nmr=giao" in the .com file
    nmr_list = ["C1", "C4", "H5"]
    df = gp.get_nmr(df, nmr_list) 

    #---------------Distance--------------------------
    #distance between 2 atoms
    dist_list_of_lists = [["O2", "C1"], ["O3", "H5"], ["C4", "C1"]]
    df = gp.get_distance(df, dist_list_of_lists) 

    #---------------Angle-----------------------------
    #angle between 3 atoms
    angle_list_of_lists = [["O3", "C1", "O2"], ["C4", "C1", "O3"]]
    df = gp.get_angles(df, angle_list_of_lists) 

    #---------------Dihedral--------------------------
    #dihedral angle between 4 atoms
    dihedral_list_of_lists = [["O2", "C1", "O3", "H5"], ["C4", "C1", "O3", "H5"]]
    df = gp.get_dihedral(df, dihedral_list_of_lists) 

    #---------------Vbur Scan-------------------------
    #uses morfeus to calculate the buried volume at a series of radii (including hydrogens)
    #inputs: dataframe, list of atoms, start_radius, end_radius, and step_size
    #if you only want a single radius, put the same value for start_radius and end_radius (keep step_size > 0)
    vbur_list = ["C1", "C4"]
    df = gp.get_vbur_scan(df, vbur_list, 2, 4, 0.5)
        
    #---------------Sterimol morfeus------------------
    #uses morfeus to calculate Sterimol L, B1, and B5 values
    #NOTE: this is much faster than the corresponding DBSTEP function (recommendation: use as default/if you don't need Sterimol2Vec)
    sterimol_list_of_lists = [["O3", "H5"], ["C1", "C4"]]
    df = gp.get_sterimol_morfeus(df, sterimol_list_of_lists) 

    #---------------Buried Sterimol-------------------
    #uses morfeus to calculate Sterimol L, B1, and B5 values within a given sphere of radius r_buried
    #atoms outside the sphere + 0.5 vdW radius are deleted and the Sterimol vectors are calculated
    #for more information: https://kjelljorner.github.io/morfeus/sterimol.html
    #inputs: dataframe, list of atom pairs, r_buried
    sterimol_list_of_lists = [["C1", "C4"]]
    df = gp.get_buried_sterimol(df, sterimol_list_of_lists, 5.5) 

    #---------------Sterimol DBSTEP-------------------
    #uses DBSTEP to calculate Sterimol L, B1, and B5 values
    #default grid point spacing (0.05 Angstrom) is used (can use custom spacing or vdw radii in the get_properties_functions script)
    #more info here: https://github.com/patonlab/DBSTEP
    #NOTE: this takes longer than the morfeus function (recommendation: only use this if you need Sterimol2Vec)
    sterimol_list_of_lists = [["O3", "H5"]]
    df = gp.get_sterimol_dbstep(df, sterimol_list_of_lists) 

    #---------------Sterimol2Vec----------------------
    #uses DBSTEP to calculate Sterimol Bmin and Bmax values at intervals from 0 to end_radius, with a given step_size 
    #default grid point spacing (0.05 Angstrom) is used (can use custom spacing or vdw radii in the get_properties_functions script)
    #more info here: https://github.com/patonlab/DBSTEP
    #inputs: dataframe, list of atom pairs, end_radius, and step_size
    sterimol2vec_list_of_lists = [["C1", "C4"]]
    df = gp.get_sterimol2vec(df, sterimol2vec_list_of_lists, 1, 1.0) 

    #---------------Pyramidalization------------------
    #uses morfeus to calculate pyramidalization based on the 3 atoms in closest proximity to the defined atom
    #collects values based on two definitions of pyramidalization
    #details on these values can be found here: https://kjelljorner.github.io/morfeus/pyramidalization.html
    pyr_list = ["C1", "C4"]
    df = gp.get_pyramidalization(df, pyr_list)

    #---------------Plane Angle-----------------------
    #plane angle between 2 planes (each defined by 3 atoms)
    planeangle_list_of_lists = [["O2", "C1", "O3", "H5", "C1", "C4"], ["O2", "C1", "O3", "H5", "C1", "C4"]]
    df = gp.get_planeangle(df, planeangle_list_of_lists) 

    pd.options.display.max_columns = None

    #for numerically named compounds, prefix is any text common to all BEFORE the number and suffix is common to all AFTER the number
    #this is a template for our files that are all named "AcXXX_clust-X.log" or "AcXXX_conf-X.log"
    prefix = "Ac" 
    suffix = "_"

    #columns that provide atom mapping information are dropped
    atom_columns_to_drop = ["C1", "O2", "O3", "C4", "H5"]

    #title of the column for the energy you want to use for boltzmann averaging and lowest E conformer determination
    energy_col_header = "G(T)_spc(Hartree)"


    energy_cutoff = 4.2 #specify energy cutoff in kcal/mol to remove conformers above this value before post-processing
    verbose = False #set to true if you'd like to see info on the nunmber of conformers removed for

    #this is a template for our files that are all named "AcXXX_clust-X.log"

    compound_list = []
    
    for index, row in df.iterrows():
        log_file = row['log_name'] #read file name from df
        prefix_and_compound = log_file.split(str(suffix)) #splits to get "AcXXX" (entry O) (and we don't use the "clust-X" (entry 1))
        compound = prefix_and_compound[0].split(str(prefix)) #splits again to get "XXX" (entry 1) (and we don't use the empty string "" (entry 0))
        compound_list.append(compound[1])

    compound_list = list(set(compound_list)) #removes duplicate stuctures that result from having conformers of each
    compound_list.sort() #reorders numerically (not sure if it reorders alphabetically)
    print(compound_list)

    #this should generate a list that looks like this: ['24', '27', '34', '48']

    all_df_master = pd.DataFrame(columns=[])
    properties_df_master = pd.DataFrame(columns=[])

    for compound in compound_list: 
        #defines the common start to all files using the input above 
        substring = str(prefix) + str(compound) + str(suffix)
        
        #makes a data frame for one compound at a time for post-processing
        valuesdf = df[df["log_name"].str.startswith(substring)]
        valuesdf = valuesdf.drop(columns = atom_columns_to_drop)
        valuesdf = valuesdf.reset_index(drop = True)  #you must re-index otherwise the 2nd, 3rd, etc. compounds fail
    
        #define columns that won't be included in summary properties or are treated differently because they don't make sense to Boltzmann average
        non_boltz_columns = ["G(Hartree)","∆G(Hartree)","∆G(kcal/mol)", "e^(-∆G/RT)","Mole Fraction"] #don't boltzman average columns containing these strings in the column label
        reg_avg_columns = ['CPU_time_total(hours)', 'Wall_time_total(hours)'] #don't boltzmann average these either, we average them in case that is helpful
        gv_extra_columns = ['E_spc (Hartree)', 'H_spc(Hartree)', 'T', 'T*S', 'T*qh_S', 'ZPE(Hartree)', 'qh_G(T)_spc(Hartree)', "G(T)_spc(Hartree)"]
        gv_extra_columns.remove(str(energy_col_header))
        
        #calculate the summary properties based on all conformers (Boltzmann Average, Minimum, Maximum, Boltzmann Weighted Std)
        valuesdf["∆G(Hartree)"] = valuesdf[energy_col_header] - valuesdf[energy_col_header].min()
        valuesdf["∆G(kcal/mol)"] = valuesdf["∆G(Hartree)"] * 627.5
        valuesdf["e^(-∆G/RT)"] = np.exp((valuesdf["∆G(kcal/mol)"] * -1000) / (1.987204 * 298.15)) #R is in cal/(K*mol)
        valuesdf["Mole Fraction"] = valuesdf["e^(-∆G/RT)"] / valuesdf["e^(-∆G/RT)"].sum()
        initial = len(valuesdf.index)
        if verbose: 
            print(prefix + str(compound))
            #display(valuesdf)
            print("Total number of conformers = ", initial)
        valuesdf.drop(valuesdf[valuesdf["∆G(kcal/mol)"] >= energy_cutoff].index, inplace=True) #E cutoff applied here
        valuesdf = valuesdf.reset_index(drop = True) #resetting indexes
        final = len(valuesdf.index) 
        if verbose: 
            print("Number of conformers above ", energy_cutoff, " kcal/mol: ", initial-final)
        values_boltz_row = []
        values_min_row = []
        values_max_row = []
        values_boltz_stdev_row =[]
        values_range_row = []
        values_exclude_columns = []
        
        for column in valuesdf:
            if "log_name" in column:
                values_boltz_row.append("Boltzmann Averages")
                values_min_row.append("Ensemble Minimum")
                values_max_row.append("Ensemble Maximum")
                values_boltz_stdev_row.append("Boltzmann Standard Deviation")
                values_range_row.append("Ensemble Range")
                values_exclude_columns.append(column) #used later to build final dataframe
            elif any(phrase in column for phrase in non_boltz_columns) or any(phrase in column for phrase in gv_extra_columns):
                values_boltz_row.append("")
                values_min_row.append("")
                values_max_row.append("")
                values_boltz_stdev_row.append("")
                values_range_row.append("")
            elif any(phrase in column for phrase in reg_avg_columns):
                values_boltz_row.append(valuesdf[column].mean()) #intended to print the average CPU/wall time in the boltz column
                values_min_row.append("")
                values_max_row.append("")
                values_boltz_stdev_row.append("")
                values_range_row.append("")
            else:
                valuesdf[column] = pd.to_numeric(valuesdf[column]) #to hopefully solve the error that sometimes occurs where the float(Mole Fraction) cannot be mulitplied by the string(property)
                values_boltz_row.append((valuesdf[column] * valuesdf["Mole Fraction"]).sum())
                values_min_row.append(valuesdf[column].min())
                values_max_row.append(valuesdf[column].max())
                values_range_row.append(valuesdf[column].max() - valuesdf[column].min())

                
                # this section generates the weighted std deviation (weighted by mole fraction) 
                # formula: https://www.statology.org/weighted-standard-deviation-excel/
        
                boltz = (valuesdf[column] * valuesdf["Mole Fraction"]).sum() #number
                delta_values_sq = []
        
                #makes a list of the "deviation" for each conformer           
                for index, row in valuesdf.iterrows(): 
                    value = row[column]
                    delta_value_sq = (value - boltz)**2
                    delta_values_sq.append(delta_value_sq)
                
                #w is list of weights (i.e. mole fractions)
                w = list(valuesdf["Mole Fraction"])
                wstdev = np.sqrt( (np.average(delta_values_sq, weights=w)) / (((len(w)-1)/len(w))*np.sum(w)) )
                if len(w) == 1: #if there is only one conformer in the ensemble, set the weighted standard deviation to 0 
                    wstdev = 0
                #np.average(delta_values_sq, weights=w) generates sum of each (delta_value_sq * mole fraction)
                
                values_boltz_stdev_row.append(wstdev)   
            
    valuesdf.loc[len(valuesdf)] = values_boltz_row
    valuesdf.loc[len(valuesdf)] = values_boltz_stdev_row
    valuesdf.loc[len(valuesdf)] = values_min_row
    valuesdf.loc[len(valuesdf)] = values_max_row
    valuesdf.loc[len(valuesdf)] = values_range_row

    #final output format is built here:
    explicit_order_front_columns = ["log_name", energy_col_header,"∆G(Hartree)","∆G(kcal/mol)","e^(-∆G/RT)","Mole Fraction"]
    
    #reorders the dataframe using front columns defined above
    valuesdf = valuesdf[explicit_order_front_columns + [col for col in valuesdf.columns if col not in explicit_order_front_columns and col not in values_exclude_columns]]
    
    #determine the index of the lowest energy conformer
    low_e_index = valuesdf[valuesdf["∆G(Hartree)"] == 0].index.tolist()
    
    #copy the row to a new_row with the name of the log changed to Lowest E Conformer
    new_row = valuesdf.loc[low_e_index[0]]
    new_row['log_name'] = "Lowest E Conformer"   
    valuesdf =  valuesdf.append(new_row, ignore_index=True)

    #------------------------------EDIT THIS SECTION IF YOU WANT A SPECIFIC CONFORMER----------------------------------  
    #if you want all properties for a conformer with a particular property (i.e. all properties for the Vbur_min conformer)
    #this template can be adjusted for min/max/etc. 
    
    #find the index for the min or max column:
    ensemble_min_index = valuesdf[valuesdf["log_name"] == "Ensemble Minimum"].index.tolist()
    
    #find the min or max value of the property (based on index above)
    #saves the value in a list (min_value) with one entry (this is why we call min_value[0])
    min_value = valuesdf.loc[ensemble_min_index, "%Vbur_C4_3.0Å"].tolist()   
    vbur_min_index = valuesdf[valuesdf["%Vbur_C4_3.0Å"] == min_value[0]].index.tolist()
    
    #copy the row to a new_row with the name of the log changed to Property_min_conformer
    new_row = valuesdf.loc[vbur_min_index[0]]
    new_row['log_name'] = "%Vbur_C4_3.0Å_min_Conformer"   
    valuesdf =  valuesdf.append(new_row, ignore_index=True)
    #--------------------------------------------------------------------------------------------------------------------    
    
    #appends the frame to the master output
    all_df_master = pd.concat([all_df_master, valuesdf])
    
    #drop all the individual conformers
    dropindex = valuesdf[valuesdf["log_name"].str.startswith(substring)].index
    valuesdf = valuesdf.drop(dropindex)
    valuesdf = valuesdf.reset_index(drop = True)
    
    #display(valuesdf)   
    
    #drop the columns created to determine the mole fraction and some that 
    valuesdf = valuesdf.drop(columns = explicit_order_front_columns)
    try:
        valuesdf = valuesdf.drop(columns = gv_extra_columns)
    except:
        pass
    try:
        valuesdf = valuesdf.drop(columns = reg_avg_columns)
    except:
        pass
        
    #---------------------THIS MAY NEED TO CHANGE DEPENDING ON HOW YOU LABEL YOUR COMPOUNDS------------------------------  
    compound_name = prefix + str(compound) 
    #--------------------------------------------------------------------------------------------------------------------      

    properties_df = pd.DataFrame({'Compound_Name': [compound_name]})
    
    #builds a dataframe (for each compound) by adding summary properties as new columns
    for (columnName, columnData) in valuesdf.iteritems():
        #the indexes need to match the values dataframe - display it to double check if you need to make changes 
        #(uncomment the display(valuesdf) in row 124 of this cell)
        properties_df[str(columnName) + "_Boltz"] = [columnData.values[0]]
        properties_df[str(columnName) + "_Boltz_stdev"] = [columnData.values[1]]
        properties_df[str(columnName) + "_min"] = [columnData.values[2]]
        properties_df[str(columnName) + "_max"] = [columnData.values[3]]
        properties_df[str(columnName) + "_range"] = [columnData.values[4]]
        properties_df[str(columnName) + "_low_E"] = [columnData.values[5]]
        
        #if you're collecting properties for a specific conformer, add these here (note the index)
        #example:
        properties_df[str(columnName) + "_V_bur_min"] = [columnData.values[6]]
        
        #if you only want a table with Boltz, you can comment out the other summary properties to generate a Boltz spreadsheet
        #of if you don't want to collect range, etc.
    #concatenates the individual acid properties df into the master properties df
    properties_df_master = pd.concat([properties_df_master, properties_df], axis = 0)

    all_df_master = all_df_master.reset_index(drop = True)
    properties_df_master = properties_df_master.reset_index(drop = True)

    display(properties_df_master.head())
    display(all_df_master)

    return df

extract_parameters("molecules.sdf", "c-Br")
