import re
import os

def get_element():
    element_dict = {} # {element_name: elements}
    with open(os.path.dirname(__file__)+'/element.ini') as f:
        line = f.readline()
        number = int(re.search('\d+', line).group())
        for i in range(number):
            line = re.split("=|\n", f.readline())[1]
            line = re.split("\|", line)
            element_dict[line[0]] = ([float(s) for s in re.findall("\d+\.?\d*", line[1])], [float(s) for s in re.findall("\d+\.?\d*", line[2])])
    return element_dict
    