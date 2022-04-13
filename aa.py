import re
import os
from .element import get_element

def get_aa(mode="mono"):
    element_dict = get_element()
    aa_dict = {} # {aa_name: mono_mass}
    with open(os.path.dirname(__file__)+'/aa.ini') as f:
        line = f.readline()
        number = int(re.search('\d+', line).group())
        line = f.readline()
        if mode == "mono":
            for i in range(number):
                line = re.split("=|\n", f.readline())[1]
                line = re.split("\|", line)
                items = re.split("\(|\)", line[1].strip(")"))
                aa_mass = 0.0
                for j in range(int(len(items)/2)):
                    element_mass = element_dict[items[j*2]][0][0] # mono mass
                    aa_mass += element_mass * int(items[j*2+1])
                aa_dict[line[0]] = aa_mass
        elif mode == "avg":
            for i in range(number):
                line = re.split("=|\n", f.readline())[1]
                line = re.split("\|", line)
                items = re.split("\(|\)", line[1].strip(")"))
                aa_mass = 0.0
                for j in range(int(len(items)/2)):
                    for element_mass, element_abundance in zip(*element_dict[items[j*2]]):
                        aa_mass += element_mass * element_abundance * int(items[j*2+1])
                aa_dict[line[0]] = aa_mass
        return aa_dict
get_aa("avg")
