# import muselsl.viewer_v2 as viewing
from muselsl import record
from record_openbci_direct import record_obci_direct
import sys
import re
import os
import time
import json
import math
from statistics import mean
import shutil

experiment_config_location = 'C:\\Nir\\vr_dda_fps\\Assets\\Python\\experiment_config.json'
with open(experiment_config_location) as f:
    config = json.load(f)


# this app is called from command line with following arguments:
#duration of recording
#name of session log file
#name of recording file
#recording device type

def cleantxtFiles():
    target = config["patientname"]
    if not os.path.exists(target):
        os.makedirs(target)
    shutil.copyfile(config["LowThresholdLocation"], target + "\\LowThreshold.txt")
    shutil.copyfile(config["HighThresholdLocation"], target + "\\HighThreshold.txt")
    with open(config["LowThresholdLocation"], 'w') as fin:
        fin.write("")
    with open(config["HighThresholdLocation"], 'w') as fin:
        fin.write("")
    print("Text copied and cleaned")

def setTEILow(HighorLow):
    if HighorLow == "TEILow":
        with open(config["LowThresholdLocation"], 'r') as fin:
            data = [str(x) for x in fin.read().split('\n')]
        data = [float(i) for i in data[:-1]]
        data = [x for x in data if math.isnan(x) == False]
        average = mean(data)
        if math.isnan(average):
            average = 0.5
    else:
        with open(config["HighThresholdLocation"], 'r') as fin:
            data = [str(x) for x in fin.read().split('\n')]
        data = [float(i) for i in data[:-1]]
        data = [x for x in data if math.isnan(x) == False]
        average = mean(data)
        if math.isnan(average):
            average = 0.8
    with open(experiment_config_location) as f:
        data = json.load(f)
    data[HighorLow] = average
    if data['TEIHigh'] < data['TEILow']:
        data['TEIHigh'] = 0.8
    with open(experiment_config_location, 'w') as f:
        json.dump(data, f)
        print("Finished writing to config")

if __name__ == '__main__':
    #
    # logfile = sys.argv[2]
    # logfile = logfile[1:-1]
    #
    # recording_filename = sys.argv[3]
    # recording_filename = recording_filename[1:-1]
    #
    # duration = sys.argv[1]
    # duration = re.findall('[0-9]+', duration[0])
    # device_type = sys.argv[4]
    # device_type = device_type[1:-1]
    print(sys.argv[1])
    print(type(int(sys.argv[1])))
    duration = int(sys.argv[1])

    # if device_type == "OPENBCI":
    #     record_obci_direct(int(numbers[0]), logfile, recording_filename, json.load(open('experiment_config.json'))["OPENBCI_COM_PORT"])
    # else:

    patientname = config["patientname"]
    # duration = config["Duration"]
    # duration = 169
    print(os.path.abspath(os.getcwd()))
    # recording_filename = '1_1'
    if duration == config["Lowtimeframe"]:
        cleantxtFiles()
    record(duration)
    if duration == config["Lowtimeframe"]:
        setTEILow('TEILow')
    else:
        setTEILow('TEIHigh')
    print("closing recorder session.")
    #exit()
    sys.exit(0)
