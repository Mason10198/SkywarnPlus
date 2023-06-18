#!/usr/bin/python3
# SkyControl.py
# A Control Script for SkywarnPlus v0.2.2
# by Mason Nelson (N5LSN/WRKF394)
#
# This script allows you to change the value of specific keys in the SkywarnPlus config.yaml file.
# It's designed to enable or disable certain features of SkywarnPlus from the command line.
# It is case-insensitive, accepting both upper and lower case parameters.
#
# Usage: SkyControl.py <key> <value>
# Example: SkyControl.py sayalert false
# This will set 'SayAlert' to 'False' in the config.yaml file.

import os
import shutil
import sys
import yaml
import subprocess
from pathlib import Path


# Define a function to change the CT
def changeCT(ct):
    tone_dir = config["CourtesyTones"].get(
        "ToneDir", os.path.join(str(SCRIPT_DIR), "SOUNDS/TONES")
    )
    ct1 = config["CourtesyTones"]["Tones"]["CT1"]
    ct2 = config["CourtesyTones"]["Tones"]["CT2"]
    wx_ct = config["CourtesyTones"]["Tones"]["WXCT"]
    rpt_ct1 = config["CourtesyTones"]["Tones"]["RptCT1"]
    rpt_ct2 = config["CourtesyTones"]["Tones"]["RptCT2"]

    if ct == "normal":
        src_file = os.path.join(tone_dir, ct1)
        dest_file = os.path.join(tone_dir, rpt_ct1)
        shutil.copyfile(src_file, dest_file)

        src_file = os.path.join(tone_dir, ct2)
        dest_file = os.path.join(tone_dir, rpt_ct2)
        shutil.copyfile(src_file, dest_file)
        return True  # Indicate that CT was changed to normal
    elif ct == "wx":
        src_file = os.path.join(tone_dir, wx_ct)
        dest_file = os.path.join(tone_dir, rpt_ct1)
        shutil.copyfile(src_file, dest_file)

        src_file = os.path.join(tone_dir, wx_ct)
        dest_file = os.path.join(tone_dir, rpt_ct2)
        shutil.copyfile(src_file, dest_file)
        return False  # Indicate that CT was changed to wx
    else:
        print("Invalid CT value. Please provide either 'wx' or 'normal'.")
        sys.exit(1)


# Define a function to change the ID
def changeID(id):
    id_dir = config["IDChange"].get("IDDir", os.path.join(SCRIPT_DIR, "ID"))
    normal_id = config["IDChange"]["IDs"]["NormalID"]
    wx_id = config["IDChange"]["IDs"]["WXID"]
    rpt_id = config["IDChange"]["IDs"]["RptID"]

    if id == "normal":
        src_file = os.path.join(id_dir, normal_id)
        dest_file = os.path.join(id_dir, rpt_id)
        shutil.copyfile(src_file, dest_file)
        return True  # Indicate that ID was changed to normal
    elif id == "wx":
        src_file = os.path.join(id_dir, wx_id)
        dest_file = os.path.join(id_dir, rpt_id)
        shutil.copyfile(src_file, dest_file)
        return False  # Indicate that ID was changed to wx
    else:
        print("Invalid ID value. Please provide either 'wx' or 'normal'.")
        sys.exit(1)


# Define valid keys and corresponding audio files
VALID_KEYS = {
    "enable": {
        "key": "Enable",
        "section": "SKYWARNPLUS",
        "true_file": "SWP85.wav",
        "false_file": "SWP86.wav",
    },
    "sayalert": {
        "key": "SayAlert",
        "section": "Alerting",
        "true_file": "SWP87.wav",
        "false_file": "SWP88.wav",
    },
    "sayallclear": {
        "key": "SayAllClear",
        "section": "Alerting",
        "true_file": "SWP89.wav",
        "false_file": "SWP90.wav",
    },
    "tailmessage": {
        "key": "Enable",
        "section": "Tailmessage",
        "true_file": "SWP91.wav",
        "false_file": "SWP92.wav",
    },
    "courtesytone": {
        "key": "Enable",
        "section": "CourtesyTones",
        "true_file": "SWP93.wav",
        "false_file": "SWP94.wav",
    },
    "idchange": {
        "key": "Enable",
        "section": "IDChange",
        "true_file": "SWP83.wav",
        "false_file": "SWP84.wav",
    },
    "alertscript": {
        "key": "Enable",
        "section": "AlertScript",
        "true_file": "SWP81.wav",
        "false_file": "SWP82.wav",
    },
    "changect": {
        "key": "",
        "section": "",
        "true_file": "SWP79.wav",
        "false_file": "SWP80.wav",
        "available_values": ["wx", "normal"],
    },
    "changeid": {
        "key": "",
        "section": "",
        "true_file": "SWP77.wav",
        "false_file": "SWP78.wav",
        "available_values": ["WX", "NORMAL"],
    },
}

# Get the directory of the script
SCRIPT_DIR = Path(__file__).parent.absolute()

# Get the configuration file
CONFIG_FILE = SCRIPT_DIR / "config.yaml"

# Check if the correct number of arguments are passed
if len(sys.argv) != 3:
    print("Incorrect number of arguments. Please provide the key and the new value.")
    print("Usage: python3 {} <key> <value>".format(sys.argv[0]))
    sys.exit(1)

# The input key and value
key, value = sys.argv[1:3]

# Make sure the provided key is valid
if key not in VALID_KEYS:
    print("The provided key does not match any configurable item.")
    sys.exit(1)

# Validate the provided value
if key in ["changect", "changeid"]:
    if value not in VALID_KEYS[key]["available_values"]:
        print(
            "Invalid value for {}. Please provide either {} or {}".format(
                key,
                VALID_KEYS[key]["available_values"][0],
                VALID_KEYS[key]["available_values"][1],
            )
        )
        sys.exit(1)
else:
    if value not in ["true", "false", "toggle"]:
        print("Invalid value. Please provide either 'true' or 'false' or 'toggle'.")
        sys.exit(1)

# Load the config file
with open(str(CONFIG_FILE), "r") as f:
    config = yaml.safe_load(f)

if key == "changect":
    value = changeCT(value)
elif key == "changeid":
    value = changeID(value)
else:
    # Convert the input value to boolean if not 'toggle'
    if value != "toggle":
        value = value.lower() == "true"

    # Check if toggle is required
    if value == "toggle":
        current_value = config[VALID_KEYS[key]["section"]][VALID_KEYS[key]["key"]]
        value = not current_value

    # Update the key in the config
    config[VALID_KEYS[key]["section"]][VALID_KEYS[key]["key"]] = value

    # Save the updated config back to the file
    with open(str(CONFIG_FILE), "w") as f:
        yaml.dump(config, f)

# Get the correct audio file based on the new value
audio_file = VALID_KEYS[key]["true_file"] if value else VALID_KEYS[key]["false_file"]

# Play the corresponding audio message on all nodes
nodes = config["Asterisk"]["Nodes"]
for node in nodes:
    subprocess.run(
        [
            "/usr/sbin/asterisk",
            "-rx",
            "rpt localplay {} {}/SOUNDS/ALERTS/{}".format(
                node, SCRIPT_DIR, audio_file.rsplit(".", 1)[0]
            ),
        ]
    )
