
from .ion_calc import *
from .AAMass import aamass
from .xlink import xlmass
import pandas as pd
import numpy as np
import re


def format_pL_modinfo(modinfo):
    '''
    Format modinfo in pLink into a mod list
    '''

    mod_list = []
    if not modinfo == "":
        for mod_str in modinfo.split(';'):
            modname = mod_str.split('(')[0]
            site = int(mod_str.split('(')[1][:-1])
            mod_list.append( (site-1, modname) )
    return mod_list
    

def format_pL_modinfo_xl(mods_str, len_pep_1):
    '''
    Format mods_str in pLink into a mod list
    len_pep_1: length of the first peptide in xl results
    '''
    
    if mods_str == "":
        return [], []

    mp_mod1 = []
    mp_mod2 = []
    for mod_str in mods_str.split(';'):
        modname = mod_str.split('(')[0]
        site = int(mod_str.split('(')[1][:-1])
        if site > len_pep_1:
            mp_mod2.append( (site-4-len_pep_1, modname) )
        else:
            mp_mod1.append( (site-1, modname) )

    return mp_mod1, mp_mod2


def format_pF_modinfo(modinfo):
    items = modinfo.split(";")
    modlist = []
    for mod in items:
        if mod != '':
            site, modname = mod.split(",")
            site = int(site)
            modlist.append( (site, modname) )
    return modlist

def format_linker_mass_xl(seq_length, linker, linksite, pepmass=0):
    '''Calc xlinker mass info and format it with pepmass into a list'''
    xlmassinfo = [0]*(seq_length+2)
    if xlmass.is_cleavable(linker):
        xlmassinfo[linksite] = xlmass.get_short_arm_mass(linker) # Short
    else:
        xlmassinfo[linksite] = pepmass + xlmass.get_linker_mass(linker)
    return xlmassinfo

def format_linker_mass_mono(xl_seq_str, linker):
    '''Get xlinker mono mass info and format it into a list'''

    line = re.split("\(|\)|\-", xl_seq_str)
    sequence, linksite = line[0], int(line[1])
    xlmassinfo = [0]*(len(sequence)+2)
    xlmassinfo[linksite] = xlmass.get_mono_mass(linker)
    return xlmassinfo

def cal_theoretical_b_y_peaks(sequence, modinfo, xlmassinfo=None):
    '''
    Return mz for b/y ions from sequence and modinfo info
    sequence: ABCDE
    modinfo: a string like "26,Carbamidomethyl[C];" or a list like [(26, Carbamidomethyl[C])]
    '''

    theoretical_peaks = {}
    bions, pepmass = calc_b_ions(sequence, modinfo, xlmassinfo)
    theoretical_peaks['b'] = bions
    theoretical_peaks['y'] = calc_y_from_b(bions, pepmass)
    #theoretical_peaks['b-ModLoss'] = calc_ion_modloss(bions, sequence, modinfo, N_term = True)
    #theoretical_peaks['y-ModLoss'] = calc_ion_modloss(theoretical_peaks['y'], sequence, modinfo, N_term = False)
    theoretical_peaks['y'].reverse()
    #theoretical_peaks['y-ModLoss'].reverse()
    return theoretical_peaks['b'], theoretical_peaks['y']#, theoretical_peaks['b-ModLoss'], theoretical_peaks['y-ModLoss']


def cal_theoretical_b_y_peaks_xl(sequence, modinfo, linker):
    '''
    Return mz for ab/ay/bb/by ions from sequence and modinfo info from pL
    sequence: QEDFYPFLKDNR(9)-VKYVTEGMR(2)
    modinfo: Oxidation[M](23)
    linker: DSSO
    '''
    
    # Split xl into two peptides
    line = re.split("\(|\)|\-", sequence) # ['LCVLHEKTPVSEK', '7', '', 'CASIQKFGER', '6', '']
    sequence1, sequence2, linksite1, linksite2 = line[0], line[3], int(line[1]), int(line[4]) # starts from 1

    # Split modinfo into two lists to the two peptides    
    modinfo1, modinfo2 = format_pL_modinfo_xl(modinfo, len(sequence.split('-')[0].split('(')[0]))

    # Calc xl mass info and deliver to two peptides as a large modification
    if xlmass.is_cleavable(linker):
        xlmassinfo1 = format_linker_mass_xl(len(sequence1), linker, linksite1)
        xlmassinfo2 = format_linker_mass_xl(len(sequence2), linker, linksite2)
    else:
        xlmassinfo1 = format_linker_mass_xl(len(sequence1), linker, linksite1, calc_pepmass(sequence2, modinfo2))
        xlmassinfo2 = format_linker_mass_xl(len(sequence2), linker, linksite2, calc_pepmass(sequence1, modinfo1))

    # Now the xl can be regarded as two single peptides with modifications. Calculate theoretical peaks.
    return cal_theoretical_b_y_peaks(sequence1, modinfo1, xlmassinfo1) + \
        cal_theoretical_b_y_peaks(sequence2, modinfo2, xlmassinfo2)


def get_theoretical_peaks_pL_xl(seq_mod_info, ions_prefix_lists):
    '''
    Calc mz for ab/ay/bb/by ions from sequence and modinfo extracted from pLink
    '''

    seq_mod_info[ions_prefix_lists] = np.array(list(map(
        lambda x, y, z: cal_theoretical_b_y_peaks_xl(x, y, z), 
            seq_mod_info['sequence'], seq_mod_info['modinfo'], seq_mod_info['linker']
        )), dtype=object)
    return seq_mod_info


def get_theoretical_peaks_pL_regular(seq_mod_info, ions_prefix_lists):
    '''
    Calc mz for ab/ay/bb/by ions from sequence and modinfo extracted from pLink
    '''

    seq_mod_info[ions_prefix_lists] = np.array(list(map(
        lambda x, y: cal_theoretical_b_y_peaks(x, format_pL_modinfo(y)), 
            seq_mod_info['sequence'], seq_mod_info['modinfo']
        )), dtype=object)
    return seq_mod_info

def get_theoretical_peaks_pL_mono(seq_mod_info, ions_prefix_lists, linker):
    '''
    Calc mz for ab/ay/bb/by ions from sequence and modinfo extracted from pLink
    '''

    seq_mod_info["linker_dict"] = np.array(list(map(
        lambda x, y: format_linker_mass_mono(x, y),
            seq_mod_info['sequence'], seq_mod_info['linker']
        )), dtype=object)

    seq_mod_info[ions_prefix_lists] = np.array(list(map(
        lambda x, y, z: cal_theoretical_b_y_peaks(x.split('(')[0], format_pL_modinfo(y), z), 
            seq_mod_info['sequence'], seq_mod_info['modinfo'], seq_mod_info["linker_dict"]
        )), dtype=object)
    return seq_mod_info


def get_theoretical_peaks_pF(seq_mod_info, ions_prefix_lists):
    '''
    Calc mz for b/y ions from sequence and modinfo extracted from pFind
    '''

    seq_mod_info[ions_prefix_lists] = np.array(list(map(
        lambda x, y: cal_theoretical_b_y_peaks(x, format_pF_modinfo(y)),
            seq_mod_info['sequence'], seq_mod_info['modinfo']
        )), dtype=object)
    return seq_mod_info

def get_theo_peaks_array(seq_mod_line, title, ions_prefix_list, cleavable_arm_mass=None):
    '''
    Calculate theoretical peaks from theoretical ions.
    For example, given mass for b, calculate mz for b with different length and charge state.
    '''
    max_charge = int(re.findall(".*?\.", title)[3].split('.')[0])

    ## Generate 1-D array from seq_mod_info and sort them
    theo_peaks_array = []
    for ions_prefix in ions_prefix_list:
        for charge in range(1, max_charge+1):
            for length, mz in enumerate(seq_mod_line[ions_prefix]):
                theo_peaks_array.append(((mz) / charge + aamass.mass_proton, 
                    f"{ions_prefix}{length+1}+{charge}"))
                '''
                theo_peaks_array.append(((mz - aamass.mass_NH3) / charge + aamass.mass_proton, 
                    f"{ions_prefix}{length+1}-NH3+{charge}"))
                theo_peaks_array.append(((mz - aamass.mass_H2O) / charge + aamass.mass_proton,
                    f"{ions_prefix}{length+1}-H2O+{charge}"))
                '''

    # Calc the peak of long arm for cleavable linkers
    if cleavable_arm_mass is not None:
        theo_peaks_array_long_arm = []
        # Get linksite
        line = re.split("\(|\)|\-", seq_mod_line["sequence"])
        len_sequence1, len_sequence2, linksite1, linksite2 = len(line[0]), len(line[3]), int(line[1]), int(line[4]) # starts from 1
        
        for strength, info in theo_peaks_array:
            # Get seqence num
            sequence_num = int(re.search("\d+", info).group())

            # If site of b less than linksite
            if info[1] == 'b':
                if info[0] == 'a':
                    if sequence_num < linksite1:
                        continue
                elif sequence_num < linksite2:
                    continue
            # If site of y less than linksite
            else:
                if info[0] == 'a':
                    if sequence_num < len_sequence1 + 1 - linksite1:
                        continue
                elif sequence_num < len_sequence2 + 1 - linksite2:
                    continue

            # Else: may exist short long arms
            charge = int(re.findall("\d+", info)[-1]) # 打表
            theo_peaks_array_long_arm.append((strength + cleavable_arm_mass / charge, info+"L"))
        theo_peaks_array = theo_peaks_array + theo_peaks_array_long_arm

    theo_peaks_array.sort(key=lambda x: x[0])
    return theo_peaks_array