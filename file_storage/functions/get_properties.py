#!apy3
#next gen: allow element input for structural parameters and get those for all relevent bonding combinations of the given elements
import os,re,subprocess
import numpy as np
from .sterimoltools import *

homo_pattern = re.compile("Alpha  occ. eigenvalues")
mo_os_pattern = re.compile("Beta  occ. eigenvalues")
zero_pattern = re.compile("zero-point Energies")
npa_pattern = re.compile("Summary of Natural Population Analysis:")
nbo_orbs_pattern = re.compile(r"(?i)Natural Bond Orbitals (Summary):")
nbo_os_pattern = re.compile("beta spin orbitals")
nbo_sop_pattern = re.compile(r"(?i)Second Order Perturbation Theory")
nmrstart_pattern = " SCF GIAO Magnetic shielding tensor (ppm):\n"
nmrend_pattern = re.compile("End of Minotr F.D.")
nmrend_pattern_os = re.compile("g value of the free electron")
dipole_pattern = "Dipole moment (field-independent basis, Debye)"
polarizability_ex_pattern = re.compile("Dipole polarizability, Alpha")
cputime_pattern = re.compile("Job cpu time:")
walltime_pattern = re.compile("Elapsed time:")
frqs_pattern = re.compile("Red. masses")
frqsend_pattern = re.compile("Thermochemistry")
volume_pattern = re.compile("Molar volume =")
cavity_pattern = re.compile("GePol: Cavity surface area")
hirshfeld_pattern = re.compile("Hirshfeld charges, spin densities, dipoles, and CM5 charges")
chelpg1_pattern = re.compile("(CHELPG)")
chelpg2_pattern = re.compile("Charges from ESP fit")
efg_pattern = re.compile("Center         ---- Electric Field Gradient ----")

float_pattern = re.compile(r"[-+]?\d*\.\d+|d+")


#Fukui:
atomnum_pattern = re.compile("NAtoms=") 
aonum_pattern = re.compile("NBasis =")
homonum_pattern = re.compile("alpha electrons")
overlap_pattern = re.compile("\*\*\* Overlap \*\*\*")
mo_pattern = re.compile("Molecular Orbital Coefficients")

periodictable = ["Bq","H","He","Li","Be","B","C","N","O","F","Ne","Na","Mg","Al","Si","P","S","Cl","Ar","K","Ca","Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Ga","Ge","As","Se","Br","Kr","Rb","Sr","Y","Zr",
             "Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","In","Sn","Sb","Te","I","Xe","Cs","Ba","La","Ce","Pr","Nd","Pm","Sm","Eu","Gd","Tb","Dy","Ho","Er","Tm","Yb","Lu","Hf","Ta","W","Re","Os","Ir","Pt","Au","Hg","Tl",
             "Pb","Bi","Po","At","Rn","Fr","Ra","Ac","Th","Pa","U","Np","Pu","Am","Cm","Bk","Cf","Es","Fm","Md","No","Lr","Rf","Db","Sg","Bh","Hs","Mt","Ds","Rg","Uub","Uut","Uuq","Uup","Uuh","Uus","Uuo","X"]

def get_logfiles(folder_path):
    logs = []
    # for file in os.listdir(folder_path):
    #     print("Checking "+file+" for log file.")
    #     if file[-4:] == ".log" or file[-4:] == ".LOG":
    #         logs.append(folder_path + "/" + file[:-4])
    #         print("Adding "+file[:-4]+" to list of log files.")
    # MODIFIED SO THAT ONLY ONE LOG FILE IS ACCEPTED INSTEAD OF THE FOLDER ITSELF
    logs.append(folder_path[:-4])
    return(logs)

def get_gjffiles(folder_path):
    gjf = []
    for file in os.listdir(folder_path):
        if file[-4:] == ".gjf":
            gjf.append(folder_path + "/" + file[:-4])
    return(gjf)

def get_coords_com(file, ext=".gjf"):
    dir = "./"
    filecont = open(dir+file+ext,'r').readlines()
    coords,elements = [],[]
    start = 999
    for l in range(len(filecont)):
        if "#" in filecont[l]:
            route = filecont[l]
        if len(filecont[l].split()) == 2 and len(filecont[l+1].split()) == 4:
            start = l+1
            chsp = filecont[l].split()
        if len(filecont[l].split()) < 2 and l > start:
            end = l
            break
    for i in range (start,end,1):
        elements.append(filecont[i].split()[0].split("-")[0])
        coords.append([filecont[i].split()[0].split("-")[0],float(filecont[i].split()[1]), float(filecont[i].split()[2]), float(filecont[i].split()[3])])    
    natoms = end - start 
    #print(natoms)     
    return(coords)

def get_outstreams(log): # gets the compressed stream information at the end of a Gaussian job
    streams = []
    starts,ends = [],[]
    error = "failed or incomplete job" # default unless "normal termination" is in file

    try:
        with open(log+".log") as f:
            loglines = f.readlines()
    except:
        with open(log+".LOG") as f:
            loglines = f.readlines()
    for i in range(len(loglines)):
        if "1\\1\\" in loglines[i]:
            starts.append(i)
        if "@" in loglines[i]:
            ends.append(i)
        if "Normal termination" in loglines[i]:
            error = ""
    if len(starts) != len(ends) or len(starts) == 0: #probably redundant
        error = "failed or incomplete job"
        return(streams,error)
    for i in range(len(starts)):
        tmp = ""
        for j in range(starts[i],ends[i]+1,1):
            tmp = tmp + loglines[j][1:-1]
        #print(tmp)
        streams.append(tmp.split("\\"))
    return(streams,error)

def get_filecont(log): # gets the entire job output
    error = "failed or incomplete job" # default unless "normal termination" is in file

    try:
        with open(log+".log") as f:
            loglines = f.readlines()
    except:
        with open(log+".LOG") as f:
            loglines = f.readlines()
    for line in loglines[::-1]:
        if "Normal termination" in line:
            error = ""
            break
    return(loglines,error)
    
def get_geom(streams): # extracts the geometry from the compressed stream
    geom = []
    for item in streams[-1][16:]:
        if item == "":
            break
        geom.append([item.split(",")[0],float(item.split(",")[-3]),float(item.split(",")[-2]),float(item.split(",")[-1])])
    return(geom)
    
def get_atominput():
    atoms = []
    query= str(input("Specify atoms of interest, separated by spaces\nEither by elemental symbol (will get all instances of this element in the molecule),\nthe atom number in the coordinates \nand / or a range of atom numbers indicated with a simple -\nMixing is possible. If a certain atom is specified by both symbol and number, it will be processed twice. \ne.g.: 1-4 9 P O\n\nFor dihedrals/angles/distances: only atom numbers.\nIf several dihedrals/angles/distances are desired, add the corresponding numbers after a space.\ne.g. 1 2 3 4 2 4 5 6\n\nFor Sterimol: Number of the base atom, then the number of the first connected atom of the residue of interest.\n\n")).split()
    #query = ["1"]#
    # check input?
    for i in query:
        if "-" in i:
            atoms = atoms + [str(a) for a in range(int(i.split("-")[0]),int(i.split("-")[1])+1)]
        else:
            atoms.append(i)
    return(atoms)
    
def write_results(content):
    with open("results.txt","a") as f:
        for log in sorted(list(content.keys())): 
            towrite = "".join(map(str,content[log]))
            f.write("%s;%s\n" %(log,towrite))
    return
    
def print_results(log,content):
    if type(content) is not str:
        content = ";".join(map(str,content))
    return(log,content)    
    
def watchout(log,error):
    if error != "":
        write_results({log:[error]})
        #print(log,"  ",error,"\n")
        return(True)
    else:
        return(False)

def get_specdata(atoms,prop): # general purpose function for NMR, NBO, possibly other data with similar output structure      
    propout = ""
    #print(atoms)
    for atom in atoms:
        if atom.isdigit():
            a = int(atom)-1
            if a <= len(prop):
                propout += prop[a][0]+str(a+1)+";"+prop[a][1]+";"
            else: continue
        elif atom.isalpha():    
            for a in range(len(prop)):
                if prop[a][0] == atom:
                    #print(prop[a][0])
                    propout += prop[a][0]+str(a+1)+";"+prop[a][1]+";"
        else: continue
    return(propout)
    
# -- Jobtypes --        
def get_route(streams,blank):
    routes = ""
    for stream in streams: 
        for item in stream:
            if "#" in item:
                routes += item+";"
    return(routes,"")

def get_e_hf(streams,no): # electronic energy of all subjobs
    e_hf = ""
    if no == 0:
        for stream in streams: 
            for item in stream:
                if "HF=" in item:
                    e_hf += item[3:] + ";" #string!    
            
        return(e_hf,"")
    elif no not in range(len(streams)):
        no = -1
    #print(stream)
    for item in streams[no]:
        if "HF=" in item:
            e_hf = item[3:] + ";" #string!    
            return(e_hf,"")
    error = "no energy found in file;"
    return("",error)

def get_homolumo(loglines,blank): # homo,lumo energies and derived values of last job in file  
    error = ""
    for line in loglines[::-1]:
        # if  mo_os_pattern.search(line):
        #     error = "Open shell system, HOMO/LUMO not meaningful."
        if  homo_pattern.search(line):
            homo = float(str.split(line)[-1])
            lumo = float(str.split(loglines[loglines.index(line)+1])[4])
            mu =  (homo+lumo)/2 # chemical potential / negative of molecular electronegativity
            eta = lumo-homo     # hardness/softness
            omega = str(round(mu**2/(2*eta),5)) + ";" # electrophilicity index
            return(str(homo)+";"+str(lumo) + ";"+str(round(mu,5)) + ";"+str(round(eta,5)) + ";"+omega,error)
    error = "no orbital information found;;"        
    return("",error)       

def get_enthalpies(filecont,blank): # Gets thermochemical data from Freq jobs
    error = "no thermochemical data found;;" 
    e_hf,ezpe,h,g = 0,0,0,0
    for i in range(len(filecont)-1):
        if zero_pattern.search(filecont[i]):
            ezpe = eval(str.split(filecont[i])[-1])
            h = eval(str.split(filecont[i+2])[-1])
            g = eval(str.split(filecont[i+3])[-1])
            e_hf = round(-eval(str.split(filecont[i-4])[-2]) + ezpe,6)
            error = ""
            break
    #evals = [e_hf,ezpe,h,g]
    evals = str(e_hf)+";"+str(g) + ";"
    return(evals,error)

def get_g_scaled(log,blank):
    error = "Some problem"
    try:
        std = subprocess.run("python -m goodvibes "+log+".log",shell=True, stdout=subprocess.PIPE)
        g_scaled = float_pattern.findall(str(std))[-1] # finds the last float in the output. this is the scaled G
        try: 
            os.remove("Goodvibes_output.dat")
        except:
            pass
        return(g_scaled+";","")
    except:
        return("",error)

def get_nimag(streams,blank):
    for stream in streams:
        for item in stream:
            if "NImag" in item:
                nimag = item[6:] + ";" #string!    
                return(nimag,"")
    error = "no frequency information found in file;"
    return("",error)
    
def get_nbo(filecont,atoms): 
    nbo,nbostart,nboout,skip = [],0,"",0
    for i in range(len(filecont)-1,0,-1):
        if re.search(nbo_os_pattern,filecont[i]) and skip == 0: 
            skip = 2            # retrieve only combined orbitals NPA in open shell molecules 
        if npa_pattern.search(filecont[i]):
            if skip != 0:
                skip = skip-1
                continue
            nbostart = i + 6
            break

    if nbostart == 0: 
        error = "no Natural Population Analysis found in file"
        return("",error+len(atoms)*2*";")
        
    for line in filecont[nbostart:]:
        if "==" in line: break
        ls = [str.split(line)[0],str.split(line)[2]]
        nbo.append(ls)
    nboout = get_specdata(atoms,nbo)

    return(nboout,"")

# phosphines    
def get_nbo_orbsP(filecont,blank): # pop=nbo
    orbitals = {
        "LP(P)_Occ":[],
        "LP(P)_E":[],
        "LP*(P)_Occ":[],
        "LP*(P)_E":[],
        "BD-S(P-C)_Occ":[],
        "BD-S(P-C)_E":[],
        "BD-S*(P-C)_Occ":[],
        "BD-S*(P-C)_E":[],
        "BD-P(P-C)_Occ":[],
        "BD-P(P-C)_E":[],
        "BD-P*(P-C)_Occ":[],
        "BD-P*(P-C)_E":[],
        "RY*(P)_Occ":[],
        "RY*(P)_E":[],
    }
    orbitals_k = {}

    for i in range(len(filecont)):
        if "NATURAL BOND ORBITAL ANALYSIS:" in filecont[i]:
            for j in range(i+10,len(filecont)):
                if " LP ( 1) P" in filecont[j]:
                    orbitals_k["percent s LP(P)"] = float(float_pattern.findall(filecont[j])[1])
                    break
        if "Natural Bond Orbitals (Summary)" in filecont[i]:
            for j in range(i,len(filecont)):
                if "P" in " ".join(re.findall("([A-Z][a-z]? *[0-9]+)",filecont[j])).split():
                    t = [float(x) for x in re.findall(r"[-+]?\d*\.\d+",filecont[j])]
                    if "LP " in filecont[j]:
                        orbitals["LP(P)_Occ"].append(t[0])
                        orbitals["LP(P)_E"].append(t[1])
                    if "LP*" in filecont[j]:
                        orbitals["LP*(P)_Occ"].append(t[0])
                        orbitals["LP*(P)_E"].append(t[1])
                    if "BD (   1)" in filecont[j]:
                        orbitals["BD-S(P-C)_Occ"].append(t[0])
                        orbitals["BD-S(P-C)_E"].append(t[1])
                    if "BD*(   1)" in filecont[j]:
                        orbitals["BD-S*(P-C)_Occ"].append(t[0])
                        orbitals["BD-S*(P-C)_E"].append(t[1])
                    if "BD (   2)" in filecont[j]:
                        orbitals["BD-P(P-C)_Occ"].append(t[0])
                        orbitals["BD-P(P-C)_E"].append(t[1])
                    if "BD*(   2)" in filecont[j]:
                        orbitals["BD-P*(P-C)_Occ"].append(t[0])
                        orbitals["BD-P*(P-C)_E"].append(t[1])
                    if "RY*" in filecont[j]:
                        orbitals["RY*(P)_Occ"].append(t[0])
                        orbitals["RY*(P)_E"].append(t[1])
            
            for orbtype in ["LP(P)","LP*(P)","BD-P(P-C)","BD-P*(P-C)","BD-S(P-C)","BD-S*(P-C)","RY*(P)"]:
                orbitals_k["no("+orbtype+")"] = len(orbitals[orbtype+"_E"])
                if orbitals_k["no("+orbtype+")"] == 0:
                    continue
                for readout in ["E","Occ"]:
                    orbitals_k[orbtype+"_avg_"+readout] = sum(orbitals[orbtype+"_"+readout]) / len(orbitals[orbtype+"_"+readout])
                    orbitals_k[orbtype+"_max_"+readout] = max(orbitals[orbtype+"_"+readout])
                    orbitals_k[orbtype+"_min_"+readout] = min(orbitals[orbtype+"_"+readout])

            orbitals_k["delta(P-MOs)_E"] = min(orbitals["BD-S*(P-C)_E"]+orbitals["BD-P*(P-C)_E"]+orbitals["LP*(P)_E"]) - max(orbitals["BD-S(P-C)_E"]+orbitals["BD-P(P-C)_E"]+orbitals["LP(P)_E"])       
            if len(orbitals["BD-S(P-C)_E"]) != 0:
                orbitals_k["delta(BD-S*-LP(P))_E"] = orbitals_k["BD-S*(P-C)_avg_E"] - orbitals_k["LP(P)_max_E"] 
            else:
                orbitals_k["delta(BD-S*-LP(P))_E"] = None

            todel = ["BD-S(P-C)_min_E","BD-P(P-C)_min_E","BD-P*(P-C)_max_E","BD-S*(P-C)_max_E","RY*(P)_max_E","RY*(P)_avg_E","LP(P)_min_E","LP(P)_avg_E","LP*(P)_max_E","LP*(P)_avg_E",
                     "BD-S(P-C)_max_Occ","BD-P(P-C)_max_Occ","BD-P*(P-C)_min_Occ","BD-S*(P-C)_min_Occ","RY*(P)_min_Occ","RY*(P)_avg_Occ","LP(P)_min_Occ","LP(P)_avg_Occ","LP*(P)_max_Occ","LP*(P)_avg_Occ",
                     "no(RY*(P))"]
            # print(orbitals_k.keys())        
            for i in todel:
                try:
                    del orbitals_k[i]
                except:
                    pass
            orbitals_k["LP(P)_E"] = orbitals_k.pop("LP(P)_max_E")
            orbitals_k["LP(P)_Occ"] = orbitals_k.pop("LP(P)_max_Occ")
            try:
                orbitals_k["LP*(P)_E"] = orbitals_k.pop("LP*(P)_min_E")
                orbitals_k["LP*(P)_Occ"] = orbitals_k.pop("LP*(P)_min_Occ")
            except:
                pass
            # print(orbitals_k.keys())
            return(orbitals_k,"")

# #Mario: allyl amines
# def get_nbo_orbs(filecont,atoms): # pop=nbo
#     elp = ""
#     bd,bds = "",""
#     for i in range(len(filecont)):
#         if "Natural Bond Orbitals (Summary)" in filecont[i]:
#             for j in range(i,len(filecont)):
#                 if "LP (   1) N " in filecont[j]:
#                     elp += ";".join(re.findall(r"[-+]?\d*\.\d+|d+",filecont[j])) +";"
#                 if "BD (   2) C  17 - C  18" in filecont[j]:
#                     bd += ";".join(re.findall(r"[-+]?\d*\.\d+|d+",filecont[j])) +";"
#                 if "BD*(   2) C  17 - C  18" in filecont[j]:
#                     bds += ";".join(re.findall(r"[-+]?\d*\.\d+|d+",filecont[j])) +";"
#                 if "----------------------" in filecont[j]:  
#                     return(elp+bd+bds,"")
#     return("0;0;0;","")

# Zayn +co sp2 N donors
def get_nbo_orbs(filecont,atoms): # pop=nbo
    orbitals = ""
    getorbs = ["BD","BD*","LP","LP*"]
    for i in range(len(filecont)):
        if "Natural Bond Orbitals (Summary)" in filecont[i] or "NATURAL BOND ORBITALS (Summary):" in filecont[i]:            
            for atom in atoms:
                for j in range(i,len(filecont)):
                    if atom in " ".join(re.findall("([A-Z][a-z]? *[0-9]+)",filecont[j])).split() and ("LP" in filecont[j] or "BD" in filecont[j]):
                        # print(filecont[j])
                        # print(re.search("[0-9]+\.[A-Z\*(0-9 ]+\)",filecont[j])[0] + " " +" - ".join(re.findall("([A-Z]+ *[0-9]+)",filecont[j])))
                        # print(re.findall(r"[-+]?\d*\.\d+",filecont[j]))
                        # print([float(x) for x in re.findall(r"[-+]?\d*\.\d+",filecont[j])])
                        # orbitals.append([re.search("[0-9]+\.[A-Z\*(0-9 ]+\)",filecont[j])[0] + " " +" - ".join(re.findall("([A-Z]+ *[0-9]+)",filecont[j]))] + [float(x) for x in re.findall(r"[-+]?\d*\.\d+|d+",filecont[j])]) # 0: number of orbital, orbital designation and atoms involved in MO; 1: occupancy, 2: energy
                        orbitals += ";".join([re.search("[0-9]+\.[A-Z\*(0-9 ]+\)",filecont[j])[0] + " " +" - ".join(re.findall("([A-Z][a-z]? *[0-9]+)",filecont[j]))] + [x for x in re.findall(r"[-+]?\d*\.\d+",filecont[j])])+";"
                    # if "----------------------" in filecont[j]:   
            return(orbitals,"")
    return("0;","")

def get_nbohomolumo(filecont,atoms):
    orbitals = []
    for i in range(len(filecont)):
        if "Natural Bond Orbitals (Summary)" in filecont[i]:
            for j in range(i,len(filecont)):
                if re.search("[0-9]+\. [A-Z]",filecont[j]):
                    orbitals.append([re.search("[0-9]+\.[A-Z\*(0-9 ]+\)",filecont[j])[0] + " " +" - ".join(re.findall("([A-Z]+ *[0-9]+)",filecont[j]))] + [float(x) for x in re.findall(r"[-+]?\d*\.\d+|d+",filecont[j])]) # 0: number of orbital, orbital designation and atoms involved in MO; 1: occupancy, 2: energy
                                            
                if "----------------------" in filecont[j]:   
                    break
            occs = sorted([x for x in orbitals if x[1]>1.2 and int(x[0][-2:])<14], key = lambda x: x[2])
            virts = sorted([x for x in orbitals if x[1]<0.8], key = lambda x: x[2])

            return(";".join([str(x) for x in occs[-2]+occs[-1]+virts[0]+virts[1]]),"")


    return("0;","")
            


# #Mario: allenoates
# def get_nbo_orbs(filecont,atoms): # pop=nbo
#     elp,bd,bds = "","",""
#     for i in range(len(filecont)):
#         if "Natural Bond Orbitals (Summary)" in filecont[i]:
#             for j in range(i,len(filecont)):
#                 if "LP (   1) O  11" in filecont[j]:
#                     elp1 = filecont[j].split()[7]
#                 if "LP (   2) O  11" in filecont[j]:
#                     elp2 = filecont[j].split()[7]
#                 if "BD (   2) C   1 - C   3" in filecont[j]:
#                     bd13 = filecont[j].split()[10]
#                 if "BD (   2) C   3 - C   4" in filecont[j]:
#                     bd34 = filecont[j].split()[10]
#                 if "BD (   2) C  10 - O  11" in filecont[j]:
#                     bdco = filecont[j].split()[10]
#                 if "BD*(   2) C   1 - C   3" in filecont[j]:
#                     bds13 = filecont[j].split()[9]
#                 if "BD*(   2) C   3 - C   4" in filecont[j]:
#                     bds34 = filecont[j].split()[9]
#                 if "BD*(   2) C  10 - O  11" in filecont[j]:
#                     bdsco = filecont[j].split()[9]
#                 if "----------------------" in filecont[j]:  
#                     return(elp1+";"+elp2+";"+bd13+";"+bd34+";"+bdco+";"+bds13+";"+bds34+";"+bdsco+";","")
#     return("0;0;0;","")

#Wenbin: Alkyl substrates
#def get_nbo_orbs(filecont,atoms): # pop=nbo
#    bd = []
#    bds = []
#    atoms = str(atoms[0])
#    for i in range(len(filecont)):
#        if "Natural Bond Orbitals (Summary)" in filecont[i]:
#            for j in range(i,len(filecont)):
#                if "BD (   1) C   "+atoms+" - H  " in filecont[j]:
#                    bd.append(float(filecont[j].split()[10]))
#                if "BD*(   1) C   "+atoms+" - H  " in filecont[j]:
#                    bds.append(float(filecont[j].split()[9]))
#                if "----------------------" in filecont[j] and len(bd)!= 0:  
#                    #print(bds)
#                    bdav = round(sum(bd)/len(bd),5)
#                    bdsav = round(sum(bds)/len(bds),5)
#                    return(str(bdav)+";"+str(min(bd))+";"+str(bdsav)+";"+str(min(bds))+";","")
#    return("0;0;0;0;","")

def get_nbo_overlap(filecont,blank): # pop=nbo
    e_chpo,e_lpoch = "",""
    error = "indicated overlap not found;"
    chpo_pattern = re.compile(r"BD.*C.*H.*BD\*.*P.*O")
    lpoch_pattern = re.compile(r"LP.*O.*BD\*.*C.*H")
    label_pattern = re.compile(r"[A-Z] +[0-9]+")
    float_pattern = re.compile(r"[-+]?\d*\.\d+|d+")
    for i in range(len(filecont)-1,1,-1):
        if nbo_sop_pattern.search(filecont[i]):
            for j in range(i+7,len(filecont)):
                if nbo_orbs_pattern.search(filecont[j]):
                    return(e_chpo+e_lpoch,error)
                if chpo_pattern.search(filecont[j]):
                    e_chpo += "-".join(label_pattern.findall(filecont[j]))+";"+float_pattern.findall(filecont[j])[0]+";"
                    error = ""
                if lpoch_pattern.search(filecont[j]):
                    e_lpoch += "-".join(label_pattern.findall(filecont[j]))+";"+float_pattern.findall(filecont[j])[0]+";"
                    error = ""
    return(e_chpo+e_lpoch,error)

def get_nmrtens(filecont,specs):
    start = 0
    nmrout = ""
    if nmrstart_pattern in filecont:
        start = filecont.index(nmrstart_pattern)+1
    else:    
        error = ";no NMR data found in file"
        return("",error+len(specs)*2*";")
    for atom in specs:
        if atom.isnumeric():
            nmrout += filecont[start+(int(atom)-1)*5].split()[1] + filecont[start+(int(atom)-1)*5].split()[0] +";"
            eigens = re.findall(r"[-+]?\d*\.\d+|d+",filecont[start+(int(atom)-1)*5+4])
            for a in range(3):
                nmrout += str(eigens[a]) + ";"
        elif atom.isalpha():
            for j in range(start,len(filecont)):
                if atom in filecont[j]:
                    nmrout += filecont[j].split()[1] + filecont[j].split()[0] +";"
                    eigens = re.findall(r"[-+]?\d*\.\d+|d+",filecont[j+4])
                    for a in range(3):
                        nmrout += str(eigens[a]) + ";"
                    continue
                if "End" in filecont[j]:
                    break
    return (nmrout,"")

def get_nmr(filecont,specs): # nmr=giao
    start,end,i = 0,0,0
    if nmrstart_pattern in filecont:
        start = filecont.index(nmrstart_pattern)+1
        for i in range(start,len(filecont),1):
            if nmrend_pattern.search(filecont[i]) or nmrend_pattern_os.search(filecont[i]):
                end = i
                break
    else:    
        error = ";no NMR data found in file"
        return("",error+len(specs)*2*";")
    atoms = int((end - start)/5)
    nmr = []
    for atom in range(atoms):
        element = str.split(filecont[start+5*atom])[1]
        shift_s = str.split(filecont[start+5*atom])[4]
        nmr.append([element,shift_s])
    nmrout = get_specdata(specs,nmr)    
    return (nmrout,"")

def get_pyramidalization(streams,atoms):
    if streams[-1][-1] == "@":
        geom = get_geom(streams)    # reading .log files
    else:
        geom = streams  # reading .gjf files
    p_out = ""
    error = ""
    for atom in atoms:
        if atom.isnumeric():
            j = int(atom)-1
            a,b = calc_pyr(j,geom)
            p_out += a
            error += b
        elif atom.isalpha():
            for j in range(len(geom)):
                if geom[j][0] == atom:
                    a,b = calc_pyr(j,geom)
                    p_out += a
                    error += b    
    return(p_out,error)    

def calc_pyr(j,geom):
    conmat = get_conmat(geom)
    bonded = []
    for i in range(len(geom)):
        if conmat[j][i]:
            bonded.append(i)
    if len(bonded) != 3:
        return(0,geom[j][0] + " is not bound to three atoms")
    a = geom[j][:4] # Atomcoords
    b = geom[bonded[0]][:4] 
    c = geom[bonded[1]][:4] 
    d = geom[bonded[2]][:4] 
    #print(a,b,c,d)

    ab = np.array(a[1:]) - np.array(b[1:])
    ac = np.array(a[1:]) - np.array(c[1:])
    ad = np.array(a[1:]) - np.array(d[1:])

    # make sure, the relative vector orientation is always the same
    bc = np.array(b[1:]) - np.array(c[1:])
    dc = np.array(d[1:]) - np.array(c[1:])
    v1 = np.cross(bc,dc)
    v2 = ab+ac+ad
    if (np.dot(v1,v2)) < 0:
        c = geom[bonded[2]][:4] 
        d = geom[bonded[1]][:4] 
        ac = np.array(a[1:]) - np.array(c[1:])
        ad = np.array(a[1:]) - np.array(d[1:])

    # angle: angle between first two bonds
    angle = np.arccos(np.dot(ab, ac) / (np.linalg.norm(ab) * np.linalg.norm(ac)))
    
    # alpha: angle between last bond and vector perpendicular to first two bonds
    cos_alpha = [0,0,0]
    cos_alpha[0] = np.dot(ad,np.cross(ac,ab))/(np.linalg.norm(np.cross(ac,ab))*np.linalg.norm(ad))
    cos_alpha[1] = np.dot(ac,np.cross(ab,ad))/(np.linalg.norm(np.cross(ab,ad))*np.linalg.norm(ac))
    cos_alpha[2] = np.dot(ab,np.cross(ad,ac))/(np.linalg.norm(np.cross(ad,ac))*np.linalg.norm(ab))
    alpha = 0.0
    for i in cos_alpha:
        alpha += np.degrees(np.arccos(i))/3
    
    # if pyramid becomes acute angled, go past 1
    if np.sign(np.dot(ab+ac,ad)) < 0:
        P = np.sin(angle)*cos_alpha[0]
    else:    
        P = 2-np.sin(angle)*cos_alpha[0]
        alpha = -alpha

    return(str("%.4f;%.4f;"%(P,alpha)),"")            

def get_planeangle(streams,atoms):
    if streams[-1][-1] == "@":
        geom = get_geom(streams)    # reading .log files
    else:
        geom = streams  # reading .gjf files
    planeangleout = ""
    error = ""
    if len(atoms)%6 != 0:
        error = str(len(atoms)) + " numbers given. Plane angles require sets of 6 numbers each " 
    for atom in atoms:
        if not atom.isdigit():
            error += atom + ": Only numbers accepted as input for plane angle "
        if int(atom) > len(geom):
            error += atom + " is out of range. Maximum valid atom number: " + str(len(geom)+1) + " "
    if error != "": return("",error+";"+int(len(atoms)/6)*";")
        
    for i in range(int(len(atoms)/6)):
        a = geom[int(atoms[6*i+0])-1][:4] # Atomcoords
        b = geom[int(atoms[6*i+1])-1][:4] 
        c = geom[int(atoms[6*i+2])-1][:4] 
        d = geom[int(atoms[6*i+3])-1][:4] 
        e = geom[int(atoms[6*i+4])-1][:4] 
        f = geom[int(atoms[6*i+5])-1][:4] 

        ab = np.array([a[1]-b[1],a[2]-b[2],a[3]-b[3]]) # Vectors
        bc = np.array([b[1]-c[1],b[2]-c[2],b[3]-c[3]])
        de = np.array([d[1]-e[1],d[2]-e[2],d[3]-e[3]])
        ef = np.array([e[1]-f[1],e[2]-f[2],e[3]-f[3]])

        n1 = np.cross(ab,bc) # Normal vectors
        n2 = np.cross(de,ef)
       
        planeangle = round(np.degrees(np.arccos(np.dot(n1,n2) / (np.linalg.norm(n1)*np.linalg.norm(n2)))),3)
        planeangle = min(abs(planeangle),abs(180-planeangle))
        planeangleout += str(a[0]+atoms[4*i+0]+" " + b[0]+atoms[4*i+1]+" " + c[0]+atoms[4*i+2]+" " + d[0]+atoms[4*i+3]) + ";" + str(planeangle) + ";"
    return(planeangleout,error)
             
def get_dihedrals(streams,atoms):
    if streams[-1][-1] == "@":
        geom = get_geom(streams)    # reading .log files
    else:
        geom = streams  # reading .gjf files
    dihedralout = ""
    error = ""
    # check input
    if len(atoms)%4 != 0:
        error = str(len(atoms)) + " numbers given. Dihedrals require sets of 4 numbers each " 
    for atom in atoms:
        if not atom.isdigit():
            error += atom + ": Only numbers accepted as input for dihedrals "
        if int(atom) > len(geom):
            error += atom + " is out of range. Maximum valid atom number: " + str(len(geom)+1) + " "
    if error != "": return("",error+";"+int(len(atoms)/4)*";")
        
    for i in range(int(len(atoms)/4)):
        a = geom[int(atoms[4*i+0])-1][:4] # Atomcoords
        b = geom[int(atoms[4*i+1])-1][:4] 
        c = geom[int(atoms[4*i+2])-1][:4] 
        d = geom[int(atoms[4*i+3])-1][:4] 

        ab = np.array([a[1]-b[1],a[2]-b[2],a[3]-b[3]]) # Vectors
        bc = np.array([b[1]-c[1],b[2]-c[2],b[3]-c[3]])
        cd = np.array([c[1]-d[1],c[2]-d[2],c[3]-d[3]])
        
        n1 = np.cross(ab,bc) # Normal vectors
        n2 = np.cross(bc,cd) - bc
        print(np.linalg.norm(np.cross(n2,bc)))

       
        dihedral = round(np.degrees(np.arccos(np.dot(n1,n2) / (np.linalg.norm(n1)*np.linalg.norm(n2)))),3)
        dihedralout += str(a[0]+atoms[4*i+0]+" " + b[0]+atoms[4*i+1]+" " + c[0]+atoms[4*i+2]+" " + d[0]+atoms[4*i+3]) + ";" + str(dihedral) + ";"
    return(dihedralout,error)

def get_angles(streams,atoms):
    if streams[-1][-1] == "@":
        geom = get_geom(streams)    # reading .log files
    else:
        geom = streams  # reading .gjf files
    anglesout = ""
    error = ""
    
    if len(atoms)%3 != 0:
        error = str(len(atoms)) + " numbers given. Angles require sets of 3 numbers each " 
    for atom in atoms:
        if not atom.isdigit():
            error += atom + ": Only numbers accepted as input for angles "
        if int(atom) > len(geom):
            error += atom + " is out of range. Maximum valid atom number: " + str(len(geom)+1) + " "
    if error != "": return("",error+int(len(atoms)/3)*";")
    
    for i in range(int(len(atoms)/3)):
        a = geom[int(atoms[3*i+0])-1][:4] # Atomcoords
        b = geom[int(atoms[3*i+1])-1][:4] 
        c = geom[int(atoms[3*i+2])-1][:4]
        ba = np.array(a[1:]) - np.array(b[1:])
        bc = np.array(c[1:]) - np.array(b[1:])      
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)

        anglesout += str(a[0]+atoms[3*i+0]+" " + b[0]+atoms[3*i+1]+" " + c[0]+atoms[3*i+2]) + ";" +str(round(np.degrees(angle),3)) + ";"
    return(anglesout,error)
    
def get_distances(streams,atoms):
    if streams[-1][-1] == "@":
        geom = get_geom(streams)    # reading .log files
    else:
        geom = streams  # reading .gjf files

    distout = ""
    error = ""
    
    if len(atoms)%2 != 0:
        error = str(len(atoms)) + " numbers given. Distances require sets of 2 numbers each " 
    for atom in atoms:
        if not atom.isdigit():
            error += atom + ": Only numbers accepted as input for distances "
        if int(atom) > len(geom):
            error += atom + " is out of range. Maximum valid atom number: " + str(len(geom)+1) + " "
    if error != "": return("",error+int(len(atoms)/2)*";")
    for i in range(int(len(atoms)/2)):
        a = geom[int(atoms[2*i+0])-1][:4] # Atomcoords
        b = geom[int(atoms[2*i+1])-1][:4] 
        ba = np.array(a[1:]) - np.array(b[1:])
        dist = round(np.linalg.norm(ba),5)
        distout += str(a[0]+atoms[2*i+0]+" " + b[0]+atoms[2*i+1]) + ";" + str(dist) + ";"
    return(distout,error)
    
def get_distances_(geom,atoms):
    a = geom[atoms[0]][:4] # Atomcoords
    b = geom[atoms[1]][:4] 
    ba = np.array(a[1:]) - np.array(b[1:])
    dist = np.linalg.norm(ba)
    return(dist)

def get_angles_(geom,atoms):
    a = geom[atoms[0]][:4] # Atomcoords
    b = geom[atoms[1]][:4] 
    c = geom[atoms[2]][:4]
    ba = np.array(a[1:]) - np.array(b[1:])
    bc = np.array(c[1:]) - np.array(b[1:])      
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(cosine_angle))
    return(angle)
    
def get_dihedrals_(geom,atoms):
    a = geom[atoms[0]][:4] # Atomcoords
    b = geom[atoms[1]][:4] 
    c = geom[atoms[2]][:4] 
    d = geom[atoms[3]][:4] 
    ab = np.array([a[1]-b[1],a[2]-b[2],a[3]-b[3]]) # Vectors
    bc = np.array([b[1]-c[1],b[2]-c[2],b[3]-c[3]])
    cd = np.array([c[1]-d[1],c[2]-d[2],c[3]-d[3]])
    n1 = np.cross(ab,bc) # Normal vectors
    n2 = np.cross(bc,cd) - bc
    dihedral = np.degrees(np.arccos(np.dot(n1,n2) / (np.linalg.norm(n1)*np.linalg.norm(n2))))
    return(dihedral)

# Sterimol: this script uses run_sterimol2. The first function is not operative in this script but left in here for compatibility with other workflows
def run_sterimol(specs): # calls a modified version of Rob Paton's Sterimol script. 
    if len(specs) == 2:
        specs.append("bondi")
    subprocess.run("sterimol.py -radii " + specs[2] + " -a1 " + specs[0] + " -a2 " + specs[1] + " all log",shell=True)
    return("check separate file results_sterimol.txt;")

def return_log(log):
    return(log,"")

def run_sterimol2(log,specs): # calls a modified version of Rob Paton's Sterimol script. 
    error = ""
    print(log)
    ext = ".log"
    file_Params = calcSterimol(log+ext, "bondi", int(specs[0]),int(specs[1]), True, True)
    lval = file_Params.lval; B1 = file_Params.B1; B5 = file_Params.newB5
    if file_Params.warn == True:
        error = ("%.2f;%.2f;%.2f;"%(lval,B1,B5)+"Warning: Atoms "+specs[0]+" and "+specs[1]+" are in cyclic structure, result may not be meaningful" )
    return("%.2f;%.2f;%.2f;;" %(lval,B1,B5),error)

def run_sterimol_confine(log,specs): # calls a modified version of Rob Paton's Sterimol script. 
    error = ""
    print(log)
    ext = ".log"
    file_Params = calcSterimol(log+ext, "bondi", int(specs[0]),int(specs[1]), False, True,False,[True,5.0,0.5])
    B1 = file_Params.B1; B5 = file_Params.newB5
    if file_Params.warn == True:
        error = ("%.2f;%.2f;"%(B1,B5)+"Warning: Atoms "+specs[0]+" and "+specs[1]+" are in cyclic structure, result may not be meaningful" )
    return("%.2f;%.2f;" %(B1,B5),error)

rcov = {"H": 0.32,"He": 0.46,"Li": 1.2,"Be": 0.94,"B": 0.77,"C": 0.75,"N": 0.71,"O": 0.63,"F": 0.64,"Ne": 0.67,"Na": 1.4,"Mg": 1.25,"Al": 1.13,"Si": 1.04,"P": 1.1,"S": 1.02,"Cl": 0.99,"Ar": 0.96,"K": 1.76,"Ca": 1.54,"Sc": 1.33,"Ti": 1.22,"V": 1.21,"Cr": 1.1,"Mn": 1.07,"Fe": 1.04,"Co": 1.0,"Ni": 0.99,"Cu": 1.01,"Zn": 1.09,"Ga": 1.12,"Ge": 1.09,"As": 1.15,"Se": 1.1,"Br": 1.14,"Kr": 1.17,"Rb": 1.89,"Sr": 1.67,"Y": 1.47,"Zr": 1.39,"Nb": 1.32,"Mo": 1.24,"Tc": 1.15,"Ru": 1.13,"Rh": 1.13,"Pd": 1.08,"Ag": 1.15,"Cd": 1.23,"In": 1.28,"Sn": 1.26,"Sb": 1.26,"Te": 1.23,"I": 1.32,"Xe": 1.31,"Cs": 2.09,"Ba": 1.76,"La": 1.62,"Ce": 1.47,"Pr": 1.58,"Nd": 1.57,"Pm": 1.56,"Sm": 1.55,"Eu": 1.51,"Gd": 1.52,"Tb": 1.51,"Dy": 1.5,"Ho": 1.49,"Er": 1.49,"Tm": 1.48,"Yb": 1.53,"Lu": 1.46,"Hf": 1.37,"Ta": 1.31,"W": 1.23,"Re": 1.18,"Os": 1.16,"Ir": 1.11,"Pt": 1.12,"Au": 1.13,"Hg": 1.32,"Tl": 1.3,"Pb": 1.3,"Bi": 1.36,"Po": 1.31,"At": 1.38,"Rn": 1.42,"Fr": 2.01,"Ra": 1.81,"Ac": 1.67,"Th": 1.58,"Pa": 1.52,"U": 1.53,"Np": 1.54,"Pu": 1.55}
def get_conmat(coords): # partially based on code from Robert Paton's Sterimol script, which based this part on Grimme's D3 code

    natom = len(coords)
    max_elem = 94
    k1 = 16.0
    k2 = 4.0/3.0
    conmat = np.zeros((natom,natom))
    for i in range(0,natom):
        if coords[i][0] not in rcov.keys():
            continue
        for iat in range(0,natom):
            if coords[iat][0] not in rcov.keys():
                continue
            if iat != i:
                dx = coords[iat][1] - coords[i][1]
                dy = coords[iat][2] - coords[i][2]
                dz = coords[iat][3] - coords[i][3]
                r = np.linalg.norm([dx,dy,dz])
                rco = rcov[coords[i][0]]+rcov[coords[iat][0]]
                rco = rco*k2
                rr=rco/r
                damp=1.0/(1.0+np.math.exp(-k1*(rr-1.0)))
                if damp > 0.85: #check if threshold is good enough for general purpose
                    conmat[i,iat],conmat[iat,i] = 1,1
    return(conmat)

def run_allsterimol(log,ref):
    try:
        ref = int(ref[0])
    except:
        ref = 1
    results = ""
    streams,error = get_outstreams(log)
    if error != "":
        return(results,error)
    coords = get_geom(streams)
    conmat = get_conmat(coords)
    for a in range(len(conmat[ref-1])):
        if conmat[ref-1][a] == 1.0:
            file_Params = calcSterimol(log+".log", "bondi",ref,a+1, True, True)
            tmp = ("%.2f;%.2f;%.2f;" %(file_Params.lval,file_Params.B1,file_Params.newB5))
            results += coords[a][0] + str(a+1) + ";" + tmp
            #lval = file_Params.lval; B1 = file_Params.B1; B5 = file_Params.newB5
            #if file_Params.warn == True:
            #    error = "%.2f;%.2f;%.2f;Warning: Atoms "+specs[0]+" and "+specs[1]+" are in cyclic structure, result may not be meaningful" %(lval,B1,B5)
    return(results,error)

def get_dipole(filecont,no):
    if no != -1: 
        for i in range(len(filecont)-1,0,-1):
            if dipole_pattern in filecont[i]:
                dipole = str.split(filecont[i+1])[-1] + ";"
                return(dipole,"")
    if no == -1: 
        for i in range(len(filecont)-1):
            if dipole_pattern in filecont[i]:
                no += 1
                dipole = str.split(filecont[i+1])[-1] + ";"
                if no == 2: return(dipole,"")
    error = "no dipole information found;"        
    return(";",error)       

def get_quadrupole(streams,blank):    
    for item in streams[-1]:
        if "Quadrupole" in item:
            q = item[11:].split(",")
            q = [float(i) for i in q]
            q_comps = np.array(([q[0],q[3],q[4]],[q[3],q[1],q[5]],[q[4],q[5],q[2]]))
            q_diag = np.linalg.eig(q_comps)[0]
            q_ampl = np.linalg.norm(q_diag)
            results = str("%.4f;%.4f;%.4f;%.4f;"%(np.max(q_diag),-(np.max(q_diag)+np.min(q_diag)),np.min(q_diag),q_ampl))
            return(results,"")
    return(";;;;","no quadrupole information found")
    
def get_polarizability(filecont,blank): # gaussian keyword: freq or polar
    for i in range(len(filecont)-1,1,-1):
        if polarizability_ex_pattern.search(filecont[i]):
            alpha_iso = float(filecont[i+4].split()[1].replace("D","E"))
            alpha_aniso = float(filecont[i+4].split()[2].replace("D","E"))
            return(str(alpha_iso) + ";" + str(alpha_aniso) + ";","")
           
    error = "no polarizability information found;"        
    return("",error)       

def get_efg(filecont,specs):
    efg = ""
    atoms = []
    atomsstart = 0
    for i in range(len(filecont)-1):
        if "Mulliken charges" in filecont[i] and atomsstart == 0:
            atomsstart = i+2
        if "Sum of Mulliken charges" in filecont[i]:
            atomsend = i
        if efg_pattern.search(filecont[i]) and "Eigenvalues" in filecont[i+2]:
            for a in specs:
                if a.isnumeric():
                    efg += filecont[int(a)+atomsstart-1].split()[1] + filecont[int(a)+atomsstart-1].split()[0] + ";" + read_efg(filecont,a,i)
                elif a.isalpha():
                    for j in range(atomsstart,atomsend):
                        if a in filecont[j].split():
                            efg += filecont[j].split()[1] + filecont[j].split()[0] + ";" + read_efg(filecont,j-atomsstart+1,i)
            return(efg,"")    
    return(";;;;;","no efg information found")

def read_efg(filecont,a,i):
    efg_xx = float(filecont[i+int(a)+3].split()[2])
    efg_yy = float(filecont[i+int(a)+3].split()[3])
    efg_zz = float(filecont[i+int(a)+3].split()[4])
    efg_ampl = np.linalg.norm(np.array(([efg_xx,efg_yy,efg_zz])))
    efg = str("%.4f;%.4f;%.4f;%.4f;"%(efg_xx,efg_yy,efg_zz,efg_ampl))
    return(efg)

def get_volume(filecont,blank):    # gaussian keyword: volume
    volume = ""
    for line in filecont:   
        if volume_pattern.search(line):
            volume = line.split()[3]
            return(volume + ";","")
    error = "not found"
    return("",error)

def get_cavity(filecont,blank): # from solvent computations, gets solvent cavity surface area and volume
    cavity_A = ""
    cavity_V = ""
    for i in range(len(filecont)-1,1,-1):
        if cavity_pattern.search(filecont[i]):
            cavity_A = filecont[i].split()[-2]
            cavity_V = filecont[i+1].split()[-2]
            return(cavity_A + ";" + cavity_V + ";","")
    error = "not found"
    return("",error)
                

def get_method(streams,blank):    # gets computational method 
    method = ""
    for stream in streams:
        method += str(stream[4])[1:]+"/"+str(stream[5]) + ";"
    return(method,"")
    
def get_version(stream,blank):    # gaussian version
    for item in stream[-1]:
        if "Version" in item:
            version = item.split("-")[1] + ";" 
            return(version,"")
    error = "not found"
    return("",error)
    
def get_time(filecont,blank):    # cpu and wall time
    cputime,walltime = 0,0
    for line in filecont:
        if cputime_pattern.search(line):
            lsplt = str.split(line)
            cputime += float(lsplt[-2])/3600 + float(lsplt[-4])/60 + float(lsplt[-6]) + float(lsplt[-8])*24
        if walltime_pattern.search(line):
            lsplt = str.split(line)
            walltime += float(lsplt[-2])/3600 + float(lsplt[-4])/60 + float(lsplt[-6]) + float(lsplt[-8])*24
    return(str(round(cputime,5)) + ";" + str(round(walltime,5)) + ";","")
    
def get_ir(filecont,specs):
# asks for sets of two atoms (number in the structure)
# checks all vibrations, keeps those where the movement of each of those two atoms is larger than "threshold"
# to limit output to the desired vibrations, indicating the appropriate frequency and intensity range in the script is required
    freqmax = 800
    freqmin = 500
    intmax = 100
    intmin = 1
    threshold = 0.1 # generally does not require changing

    frq_len = 0
    frq_end = 0
    for i in range(len(filecont)):
        if frqs_pattern.search(filecont[i]) and frq_len == 1:
            #print("2",i,frq_len)
            frq_len = i -3 - frq_start
        if frqs_pattern.search(filecont[i]) and frq_len == 0:
            #print("1",i,frq_len)
            frq_start = i-3
            frq_len = 1
        if frqsend_pattern.search(filecont[i]):    
            #print("3",i)
            frq_end = i-3
 
    nfrq = filecont[frq_end-frq_len+1].split()[-1]
    print("frq_start",frq_start)
    print("frq_end",frq_end)
    print("frq_len",frq_len)
    print((frq_end+1-frq_start)/frq_len)
    blocks = int((frq_end+1-frq_start)/frq_len)
    
    data = []   # list of objects. IR contains: IR.freq, IR.int, IR.deltas = []
    
    for i in range(blocks):
        for j in range(len(filecont[i*frq_len+frq_start].split())):
            data.append(IR(filecont,i*frq_len+frq_start,j,frq_len))
        
    results = ""
    error = ""
    
    # for i in range(natoms):
    #     if geom[i][0] == "Pd":
    #         no_pd = i
    #         break
    # for i in range(natoms):
    #     if conmat[no_pd][i] and geom[i][0] == "Cl":
    #         no_cl.append(i)
    #     if conmat[no_pd][i] and geom[i][0] == "P":
    #         no_p.append(i)


    if len(specs)%2 != 0:
        error = str(len(specs)) + " numbers given. IR data currently requires sets of 2 numbers each " 
    for i in range(int(len(specs)/2)):
        if specs[2*i].isdigit() and specs[2*i+1].isdigit():
            atom1,atom2 = int(specs[2*i])-1,int(specs[2*i+1])-1
            if int(atom1) > frq_len-7 or int(atom2) > frq_len-7:
                error += atom1+", "+atom2 + ": out of range. Maximum valid atom number: " + str(frq_len-7) + " "
        elif specs[2*i] in periodictable and specs[2*i+1] in periodictable:
            atom1,atom2 = data[0].elements.index(specs[2*i]),data[0].elements.index(specs[2*i+1]) # gets the first instance of each element in the geometry
        else:
            error += specs[2*i]+", "+specs[2*i+1] + ": Only pairs of numbers or pairs of elements accepted as input for distances "
        if error != "": return("",error+int(len(specs)/2)*";")

        for vib in range(len(data)):
            if (data[vib].deltas[atom1] > threshold and data[vib].deltas[atom2] > threshold) and data[vib].freq < freqmax and data[vib].freq > freqmin and data[vib].int > intmin and data[vib].int < intmax:
                print(data[vib].deltas[atom1],data[vib].deltas[atom2],data[vib].freq,data[vib].int)
                results += str(data[vib].freq) + ";" + str(data[vib].int) + ";"            
    return(results,"")
    
class IR:
    def __init__(self,filecont,start,col,len):
        self.freqno = int(filecont[start].split()[-3+col])
        self.freq = float(filecont[start+2].split()[-3+col])
        self.int = float(filecont[start+5].split()[-3+col])
        self.deltas = []
        atomnos = []
        for a in range(len-7):
            atomnos.append(filecont[start+7+a].split()[1])
            x = float(filecont[start+7+a].split()[3*col+2])
            y = float(filecont[start+7+a].split()[3*col+3])
            z = float(filecont[start+7+a].split()[3*col+4])
            self.deltas.append(np.linalg.norm([x,y,z]))
        self.elements = [periodictable[int(a)] for a in atomnos]

def get_fukui(file,specs):
    results,error = "",""
    # numlist[X]=
    # 0 atomnum
    # 1 aonum
    # 2 homonum
    # #3 converged
    # 4 mostart
    # 5 overlapstart
    #
    # atoms[i][X]=
    # 0 element
    # 1 index
    # 2 aostart
    # 3 aoend
    # 4 numao
    #
    # method[X]=
    # 0 "SP" / "FOpt"
    # 1 Methode/Funktional
    # 2 Bassissatz oder Gen

    filelen = len(file)
    for i in range(filelen):
        if homonum_pattern.search(file[i]):
            homonum = int(str.split(file[i])[0])
        if atomnum_pattern.search(file[i]):
            atomnum = int(str.split(file[i])[1])    
        if aonum_pattern.search(file[i]):
            aonum = int(file[i][12:16])#str.split(file[i])[1])
        if overlap_pattern.search(file[i]):
            o = i #overlap_start
            break

    for i in range(filelen-int((aonum+1)*(aonum)/5),1,-1):
        if mo_pattern.search(file[i]):
            mostart = i
            break

    #get atoms;homo-,lumo-koeffizienten
    atoms = []
    homo = []
    lumo = []
    for i in range(aonum):
        word = str.split(file[mostart+4+i])
        lumo.append(str.split(file[mostart+7+aonum+i])[-5])
        homo.append(word[-1])
        if str.isdigit(word[1]):
            atom = [word[2],int(word[1]),int(word[0]),1,1]
            atoms.append(atom)
    for i in range(atomnum-1):
        atoms[i][3] = atoms[i+1][2] - 1
        atoms[i][4] = atoms[i][3] - atoms[i][2] +1
    atoms[-1][3] = aonum
    atoms[-1][4] = aonum - atoms[-1][2] +1
    homo = np.array(homo,dtype=float)
    lumo = np.array(lumo,dtype=float)
    overlap = np.zeros((aonum,aonum),float)
    for j in range(aonum):  
        for i in range(j,aonum):
            a,b = divmod(j+1,5)
            if b != 0:
                #in Block a+1; Dieser beginnt in Zeile o+(-2.5*a^2+(aonum+3.5)*a+3)
                z = str.split(file[int(i-a*5+o-2.5*a*a+(aonum+3.5)*a+2)])[b]
            elif b == 0:
                a -= 1
                z = str.split(file[int(i-a*5+o-2.5*a*a+(aonum+3.5)*a+2)])[5]
            overlap[i][j] = float(z[:-4])*pow(10,float(z[-3:]))
            overlap[j][i] = overlap[i][j]
    numlist = [atomnum,aonum,homonum,0,mostart,o]        

    #Daten vorbereiten: MO-Koeffizienten quadrieren, Ueberlappmatrix mit MO-Koeffs multiplizieren
    homosqr = np.square(homo)
    lumosqr = np.square(lumo)
    overlap -= np.identity(numlist[1])
    procmat_homo = np.zeros((numlist[1],numlist[1]),float)
    procmat_lumo = np.zeros((numlist[1],numlist[1]),float)
    # for i in range(numlist[1]):
        # for j in range(numlist[1]):
            # procmat_homo[i][j] = overlap_0[i][j] * homo[i] * homo[j]
            # procmat_lumo[i][j] = overlap_0[i][j] * lumo[i] * lumo[j]
    procmat_homo = np.transpose(overlap * homo) * homo     
    procmat_lumo = np.transpose(overlap * lumo) * lumo        
    #Fukuis berechnen 
    fukuis_plus = []
    fukuis_minus = []
    for atom in atoms:
        plus_sum1 = np.sum(lumosqr[atom[2]-1:atom[3]])
        plus_sum2 = np.sum(np.sum(procmat_lumo[atom[2]-1:atom[3]],0))
        fukui_plus = plus_sum1 + plus_sum2
        fukuis_plus.append(fukui_plus)
        minus_sum1 = np.sum(homosqr[atom[2]-1:atom[3]])
        minus_sum2 = np.sum(np.sum(procmat_homo[atom[2]-1:atom[3]],0))
        fukui_minus = minus_sum1 + minus_sum2
        fukuis_minus.append(fukui_minus)
    for spec in specs:
        if spec.isnumeric():
            results += str("%s;%.4f;%.4f;"%(atoms[int(spec)-1][0]+str(atoms[int(spec)-1][1]),fukuis_plus[int(spec)-1],fukuis_minus[int(spec)-1]))
        elif spec.isalpha():
            for atom in atoms:
                if atom[0] == spec:
                    results += str("%s;%.4f;%.4f;"%(atom[0]+str(atom[1]),fukuis_plus[atom[1]-1],fukuis_minus[atom[1]-1]))                    
    return(results,error)   

def get_hirsh(filecont,atoms): 
    hirshstart,results = 0,""
    for i in range(len(filecont)-1,0,-1):
        if hirshfeld_pattern.search(filecont[i]):
            hirshstart = i
            break
    if hirshstart == 0: 
        error = "no Hirshfeld Population Analysis found in file"
        return("",error+len(atoms)*4*";")
    for atom in atoms:
        if atom.isnumeric():
            results += read_hirsh(atom,filecont,hirshstart)
        elif atom.isalpha():
            for j in range(hirshstart+1,len(filecont)):
                if atom in filecont[j].split():
                    results += read_hirsh(j-1-hirshstart,filecont,hirshstart)
                if "summed" in filecont[j]:
                    break
    return(results,"")         

def read_hirsh(atom,filecont,hirshstart):
    cont = filecont[hirshstart+int(atom)+1].split()
    label = cont[1] + cont[0]
    qh = cont[2]
    qcm5 = cont[7]
    d = np.linalg.norm(np.array((cont[4:8])))
    return(str("%s;%s;%s;%.5f;"%(label,qh,qcm5,d)))

def get_chelpg(filecont,atoms):
    chelpgstart,results,error,chelpg = 0,"","",False
    for i in range(len(filecont)-1,0,-1):
        if chelpg2_pattern.search(filecont[i]):
            chelpgstart = i
        if chelpg1_pattern.search(filecont[i]):
            chelpg = True
            break
    if chelpgstart != 0 and chelpg == False:
        error = "Other ESP scheme than ChelpG used in this computation"
    if chelpgstart == 0: 
        error = "no ESP Charge Analysis found in file"
    if error != "":    
        return("",error+len(atoms)*4*";")
    for atom in atoms:
        if atom.isnumeric():
            results += filecont[chelpgstart+int(atom)+2].split()[1]+filecont[chelpgstart+int(atom)+2].split()[0] + ";" + filecont[chelpgstart+int(atom)+2].split()[-1]+";"
        elif atom.isalpha():
            for j in range(chelpgstart,len(filecont)):
                if atom in filecont[j].split():
                    results += filecont[j].split()[1]+filecont[j].split()[0] + ";" + filecont[j].split()[-1]+";"
                if "Sum" in filecont[j]:
                    break
    return(results,"")

# def get_visvol(streams,atoms):
    # if streams[-1][-1] == "@":
        # geom = get_geom(streams)    # reading .log files
    # else:
        # geom = streams  # reading .gjf files

    # distout = ""
    # error = ""

    # for atom in atoms:
        # if atom.isdigit():
            # a = int(atom)-1
            # visvol_results = visvol.get_vis_vol(geom,a,radii_type = 'rcov',prox_cutoff = 3.5,ignore_H = 0,write_results = 1, plot = 0)
            # results += ";".join(visvol_results[:4])+";"
        # elif atom.isalpha():    
            # for a in range(len(geom)):
                # if geom[a][0] == atom:
                    # visvol_results = visvol.get_vis_vol(geom,a,radii_type = 'rcov',prox_cutoff = 3.5,ignore_H = 0,write_results = 1, plot = 0)
                    # results += ";".join(visvol_results[:4])+";"
        # else: continue

    # return(results,"")



#---------------------------------
jobtypes = {
"e":        [" e:        E_HF (final electronic energy) of each job in the file                   - n(jobs)",get_e_hf,get_outstreams],
"homo":     [" homo:     E(HOMO), E(LUMO), mu, eta, omega from the last relevant job in the file  - 5",get_homolumo,get_filecont],
"g":        [" g:        Thermochemical data. Output: E_HF, G. [freq]                             - 2",get_enthalpies,get_filecont],
"gscaled":  [" gscaled:  Free energy scaled w quasi-harmonic correction. Needs Paton's GoodVibes  - 1",get_g_scaled,return_log],
"nimag":    [" nimag:    Number of imaginary frequencies from Freq. Must be 0 for a ground state  - 1",get_nimag,get_outstreams],
"nbo":      [" nbo:      Natural charge based on NBO [pop=nbo]                                    - n(extra input)",get_nbo,get_filecont,get_atominput],
"nborbs":   [" nborbs:   Natural orbitals [pop=nbo]                                               - 4*n(extra input)",get_nbo_orbs,get_filecont,get_atominput],
"nborbsP":  [" nborbsP:   Natural orbitals of P  [pop=nbo]                                        - ",get_nbo_orbsP,get_filecont],
"nmr":      [" nmr:      Isotropic NMR shift [nmr]                                                - n(extra input)",get_nmr,get_filecont,get_atominput],
"nmrtens":  [" nmrtens:  Eigenvalues of the Anisotropic NMR shift tensor [nmr]                    - 3*n(extra input)",get_nmrtens,get_filecont,get_atominput],
"planeangle": [" planeangle: Angle between two planes (requires sets of 6 atoms, 3 for each plane)  - n(extra input)",get_planeangle,get_outstreams,get_atominput],
"dihedral": [" dihedral: Dihedral angles (input requires sets of 4 atoms)                         - n(extra input)",get_dihedrals,get_outstreams,get_atominput],
"angle":    [" angle:    Angles (input requires sets of 3 atoms)                                  - n(extra input)",get_angles,get_outstreams,get_atominput],
"dist":     [" dist:     Distances (input requires sets of 2 atoms)                               - n(extra input)",get_distances,get_outstreams,get_atominput],
"sterimol": [" sterimol: Sterimol L, B1, B5. Needs Paton's sterimoltools.py                       - 3",run_sterimol2,return_log,get_atominput],
"sterimol_confine": [" sterimol_confine: Sterimol B1, B5 of atoms within 5A + 0.5xVdW radius from atom1   - 2",run_sterimol_confine,return_log,get_atominput],
"dipole":   [" dipole:   Total dipole moment in Debye from the last relevant job in the file      - 1",get_dipole,get_filecont],
"polar":    [" polar:    'Exact' Polarizability from the last relevant job in the file [polar]    - 2",get_polarizability,get_filecont],
"surface":  [" surface:  Cavity surface area in Ang^2 and volume in Ang^3 from solvation model [scrf] - 2",get_cavity,get_filecont],
"ir":       [" ir:       ir [freq]                                                                - n(extra input)",get_ir,get_filecont,get_atominput],
"X":        [" X:        computational method                                                     - n(jobs)",get_method,get_outstreams],
"t":        [" t:        total computational time in hours                                        - 2",get_time,get_filecont],
"vers":     [" vers:     Gaussian Version                                                         - 1",get_version,get_outstreams],
"allsterimol": [" allsterimol: Sterimol L, B1, B5 for all substituents at the specified atom         - 3*n(subst)",run_allsterimol,return_log,get_atominput],
"fukui":    [" fukui:    Atom-condensed Fukui +/- indices [pop=regular iop(3/33=1)]               - 2*n",get_fukui,get_filecont,get_atominput],
"hirsh":    [" hirsh:    Hirshfeld charge, CM5 charge, Hirshfeld atom dipole [pop=hirshfeld]      - 4*n",get_hirsh,get_filecont,get_atominput], 
"chelpg":   [" chelpg:   ChelpG ESP charge [pop=chelpg]                                           - n",get_chelpg,get_filecont,get_atominput], 
"qpole":    [" qpole:    Quadrupole moment eigenvalues and amplitude                              - 4",get_quadrupole,get_outstreams],
"efg":      [" efg:      Electric field gradient tensor min and max eigenvalues [prop=efg]        - 2",get_efg,get_filecont,get_atominput],
"pyr":      [" pyr:      Pyramidalization of first atom wrt the next three                        - 2",get_pyramidalization,get_outstreams,get_atominput],
"route":    [" route:    Route lines                                                              - n(jobs)",get_route,get_outstreams],
"nbohomo":  [" nbohomo:  homo-1,homo,lumo,lumo+1 based on natural orbitals [pop=nbo]              - 4",get_nbohomolumo,get_filecont],

}
#entries per jobtype: 
# 0 description
# 1 main jobtype function
# 2 function for required data from logfile
# (3 function for required user input)

def main(jobs, arg_user_input, folder_path):
    readgjf = False
    with open("results.txt","w") as f:
        f.write("get_properties\n\nResults are presented in lines for all log-files in the current directory (excluding subdirectories). The semicolon-separated data can be copied into Excel using the 'Data - Text to Columns' function\n\n")
    #while True:
    error = "no input"
    if len(jobs) != 0:
        if "gjf" in jobs:  
            readgjf = True
        else:
            print(jobs)
            error = "" 
    while error != "":
        print("\n\n---------------------------------------------------------------\n\nProperties? (You can combine several, separate the input with spaces). The number indicates the amount of output in columns\n")
        for a in sorted([jobtypes[type][0] for type in jobtypes]): # print jobtype description and number
            print(a)
        jobs = str(input("\n\n")).split()#jobs = ["efg"]#
        if len(jobs) == 0:
            print("Please enter a number to select the desired property\n")
            continue
        #jobs = []    
        #for i in inp:
        #    jobs.append(i)
        error = ""
        for job in jobs:
            if job not in jobtypes:
                print("%s is not a supported choice.\n"%(job))
                error = "wrong input"

    results = {}
    if readgjf:
        logs = get_gjffiles(folder_path)
    else:
        logs = get_logfiles(folder_path)
    for log in logs:
        results[log] = []
    for job in jobs:
        userinput = 0
        print_results("\n\n\n" +jobtypes[job][0],"\n\n")
        if len(jobtypes[job]) == 4:         # for jobtypes that require extra input
            #userinput = jobtypes[job][3]()
            userinput = arg_user_input
        for log in logs:
            if readgjf:
                filecont = get_coords_com(log) # returns coords
                #filecont,error = jobtypes[job][2](log)
                error = ""
            else:
                filecont,error = jobtypes[job][2](log)
            if watchout(log,error):
                continue
            content,error = jobtypes[job][1](filecont,userinput) #5,6,7
            if error != "":
                content = error
            print_results(log,content)
            results[log].append(content)
        #print(results[log])        
    return(print_results(log, content))
        
# if __name__ == '__main__': 
#     jobs = sys.argv[1:]
#     main(jobs)       
