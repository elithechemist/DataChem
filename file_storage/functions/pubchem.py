import pubchempy as pcp
from django.contrib import messages
import re

# Should say smiles_to_name
def smiles_to_iupac(smiles):
    print("Now in smiles_to_iupac")
    try:
        print("smiles is: " + smiles + "WE ARE IN THE TRY BLOCK")
        # Generate the iupac name
        cid = pcp.get_cids(smiles, 'smiles')[0]
        compounds = pcp.Compound.from_cid(cid)

        has_common_name = False
        iupac_used = False

        for compound in compounds.synonyms:
            # Check if compound has lower case letters
            if re.search('[a-z]', compound) and ", " not in compound:
                match = compound
                has_common_name = True
                break

        if has_common_name == False:
            match = compounds.iupac_name
            iupac_used = True

        else:
            iupac = compounds.iupac_name
            if len(iupac) - len(match) < 6:
                match = iupac
                iupac_used = True      
        
        # Search for the first letter in the match
        if iupac_used == False:
            for i in range(len(match)):
                if match[i].isalpha():
                    index = i
                    break
            # See if the character at i + 1 is a letter
            if match[index + 1].isalpha():
                match = match[:i] + match[i].lower() + match[i+1:]
    except:
        name = "BLANK"            

    else:
        name = match
    
    finally:
        print("Got name as: " + name)
        return(name)
