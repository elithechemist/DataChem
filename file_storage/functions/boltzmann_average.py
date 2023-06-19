import math

def relative_abundance(energy_dict, temperature=298.15):
    # Boltzmann constant in J/K
    kb = 1.380649e-23
    
    # transform energies for stability in calculations
    min_energy = min(energy_dict.values())
    exp_energies = {key: math.exp(-(energy - min_energy) / (kb * temperature)) for key, energy in energy_dict.items()}

    # total sum of transformed energies
    total = sum(exp_energies.values())

    # calculate relative abundance for each conformer
    relative_abundance_dict = {key: energy / total for key, energy in exp_energies.items()}
    
    return relative_abundance_dict