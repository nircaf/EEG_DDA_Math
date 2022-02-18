import random
import sys
import subprocess
import time
import json
from muselsl import record
from record_openbci_direct import record_obci_direct
import re
import os
import time
import json
import math
from statistics import mean
import shutil

experiment_config_location = 'experiment_config.json'
with open(experiment_config_location) as f:
    config = json.load(f)


def cleantxtFiles():
    target = config["patientname"]
    if not os.path.exists(target):
        os.makedirs(target)
    try:
        shutil.copyfile(config["LowThresholdLocation"], target + "LowThreshold.txt")
        shutil.copyfile(config["HighThresholdLocation"], target + "HighThreshold.txt")
        with open(config["LowThresholdLocation"], 'w') as fin:
            fin.write("")
        with open(config["HighThresholdLocation"], 'w') as fin:
            fin.write("")
    except:
        print("No high&low thresh")
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


def random_math_problem(diff):
    if diff == 0:
        operators = ['+', '-']
        n1 = round(random.uniform(0.1, 10), 0)
        n2 = round(random.uniform(0.1, 10), 0)
    elif diff == 1:
        operators = ['*', '/']
        n1 = round(random.uniform(0.1, 10), 0)
        n2 = round(random.uniform(0.1, 10), 0)
    elif diff == 2:
        operators = ['+', '-']
        n1 = round(random.uniform(0.1, 10), 1)
        n2 = round(random.uniform(0.1, 10), 1)
    elif diff == 3:
        operators = ['*', '/']
        n1 = round(random.uniform(0.1, 10), 1)
        n2 = round(random.uniform(0.1, 10), 1)
    elif diff == 4:
        operators = ['+', '-']
        n1 = round(random.uniform(0.1, 10), 2)
        n2 = round(random.uniform(0.1, 10), 2)
    operator = random.choice(operators)
    if operator == "+":
        ans = n1 + n2
    elif operator == "-":
        ans = n1 - n2
    elif operator == "*":
        ans = n1 * n2
    elif operator == "/":
        ans = n1 / n2
    print("What is {} {} {}?\n".format(n1, operator, n2))
    return ans


def ask_question(diff):
    ans = random_math_problem(diff)
    response = input()
    print(type(response))
    return float(response), ans

def getAddRemove(diff):
    with open(config["LoggingLocation"], 'r') as f:
        data = [str(x) for x in f.read().split('\n')]
    if data[-1] == "add":
        diff += 1
    elif data[-1] == "remove":
        diff -=1

def mathquiz(time_end,LowHighGame):
    score = 0
    questions = 0
    if LowHighGame == "High":
        diff = 4
    else:
        diff = 0
    time_start = time.time()
    while time.time() < time_end:
        inputs = ask_question(diff)
        response = inputs[0]
        ans = inputs[1]
        if response == 'q':
            print("Okay, exiting the math quiz. Goodbye.")
            sys.exit()
        elif response == ans:
            score += 1
            questions += 1
            print("Correct!\n" + "Current score = {}".format(score) + "/{}".format(questions))
        else:
            questions += 1
            print("Incorrect :(\n" + "Correct Answer = {}\n".format(ans) + "Current score = {}".format(
                score) + "/{}".format(questions))
        if time_start+config["TEIInterval"]<time.time() and LowHighGame == "Game":
            print("reads muse log")
            diff = getAddRemove(diff)

    print("Your score was {}/{}".format(score, questions))


def openBatFile(location):
    call_with_args = location
    server_subprocessrec = subprocess.Popen(call_with_args, shell=True)

if __name__ == '__main__':
    cleantxtFiles()
    # Low thresh
    print("Setting low threshold")
    openBatFile("runLSL_recorder_set_low_thresh.bat")
    time_end = time.time() + config["Lowtimeframe"]
    mathquiz(time_end,"Low")
    setTEILow("TEILow")
    # High thresh
    print("Setting high threshold")
    openBatFile("runLSL_recorder_set_high_thresh.bat")
    time_end = time.time() + config["Hightimeframe"]
    mathquiz(time_end)
    setTEILow("TEIHigh","High")
    # Game mode
    print("Setting high threshold")
    openBatFile("runLSL_recorder_set_high_thresh.bat")
    time_end = time.time() + config["DurationAll"]
    mathquiz(time_end,"Game")
