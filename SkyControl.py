#!/usr/bin/python3

"""
SkyControl v0.4.3 by Mason Nelson
==================================
A Control Script for SkywarnPlus

This script allows you to change the value of specific keys in the SkywarnPlus config.yaml file.
It's designed to enable or disable certain features of SkywarnPlus from the command line.
It is case-insensitive, accepting both upper and lower case parameters.

Usage: SkyControl.py <key> <value>
Example: SkyControl.py sayalert false
This will set 'SayAlert' to 'False' in the config.yaml file.

This file is part of SkywarnPlus.
SkywarnPlus is free software: you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version. SkywarnPlus is distributed in the hope
that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with SkywarnPlus. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import shutil
import sys
import subprocess
from pathlib import Path
from ruamel.yaml import YAML

# Use ruamel.yaml instead of PyYAML to preserve comments in the config file
yaml = YAML()


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
    id_dir = config["IDChange"].get("IDDir", os.path.join(str(SCRIPT_DIR), "ID"))
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
        "true_file": "SWP_137.wav",
        "false_file": "SWP_138.wav",
    },
    "sayalert": {
        "key": "SayAlert",
        "section": "Alerting",
        "true_file": "SWP_139.wav",
        "false_file": "SWP_140.wav",
    },
    "sayallclear": {
        "key": "SayAllClear",
        "section": "Alerting",
        "true_file": "SWP_141.wav",
        "false_file": "SWP_142.wav",
    },
    "tailmessage": {
        "key": "Enable",
        "section": "Tailmessage",
        "true_file": "SWP_143.wav",
        "false_file": "SWP_144.wav",
    },
    "courtesytone": {
        "key": "Enable",
        "section": "CourtesyTones",
        "true_file": "SWP_145.wav",
        "false_file": "SWP_146.wav",
    },
    "idchange": {
        "key": "Enable",
        "section": "IDChange",
        "true_file": "SWP_135.wav",
        "false_file": "SWP_136.wav",
    },
    "alertscript": {
        "key": "Enable",
        "section": "AlertScript",
        "true_file": "SWP_133.wav",
        "false_file": "SWP_134.wav",
    },
    "changect": {
        "key": "",
        "section": "",
        "true_file": "SWP_131.wav",
        "false_file": "SWP_132.wav",
        "available_values": ["wx", "normal"],
    },
    "changeid": {
        "key": "",
        "section": "",
        "true_file": "SWP_129.wav",
        "false_file": "SWP_130.wav",
        "available_values": ["wx", "normal"],
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

# Convert to lower case
key = key.lower()
value = value.lower()

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
    config = yaml.load(f)

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
