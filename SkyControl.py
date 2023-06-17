#!/usr/bin/python3
# SkyControl.py
# A Control Script for SkywarnPlus v0.2.0
# by Mason Nelson (N5LSN/WRKF394)
#
# This script allows you to change the value of specific keys in the SkywarnPlus config.yaml file.
# It's designed to enable or disable certain features of SkywarnPlus from the command line.
# It is case-insensitive, accepting both upper and lower case parameters.
#
# Usage: python3 SkyControl.py <key> <value>
# Example: python3 SkyControl.py sayalert false
# This will set 'SayAlert' to 'False' in the config.yaml file.

import sys
import yaml
import subprocess
from pathlib import Path

# Define valid keys and corresponding audio files
VALID_KEYS = {
    "enable": {"key": "Enable", "section": "SKYWARNPLUS", "true_file": "SWP85.wav", "false_file": "SWP86.wav"},
    "sayalert": {"key": "SayAlert", "section": "Alerting", "true_file": "SWP87.wav", "false_file": "SWP88.wav"},
    "sayallclear": {"key": "SayAllClear", "section": "Alerting", "true_file": "SWP89.wav", "false_file": "SWP90.wav"},
    "tailmessage": {"key": "Enable", "section": "Tailmessage", "true_file": "SWP91.wav", "false_file": "SWP92.wav"},
    "courtesytone": {"key": "Enable", "section": "CourtesyTones", "true_file": "SWP93.wav", "false_file": "SWP94.wav"},
    "alertscript": {"key": "Enable", "section": "AlertScript", "true_file": "SWP81.wav", "false_file": "SWP82.wav"},
    "idchange": {"key": "Enable", "section": "IDChange", "true_file": "SWP83.wav", "false_file": "SWP84.wav"},
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

# Make sure the provided value is either 'true', 'false' or 'toggle'
if value not in ['true', 'false', 'toggle']:
    print("Invalid value. Please provide either 'true' or 'false' or 'toggle'.")
    sys.exit(1)

# Convert the input value to boolean if not 'toggle'
if value != 'toggle':
    value = value.lower() == 'true'

# Load the config file
with open(str(CONFIG_FILE), 'r') as f:
    config = yaml.safe_load(f)

# Check if toggle is required
if value == 'toggle':
    current_value = config[VALID_KEYS[key]['section']][VALID_KEYS[key]['key']]
    value = not current_value

# Update the key in the config
config[VALID_KEYS[key]['section']][VALID_KEYS[key]['key']] = value

# Save the updated config back to the file
with open(str(CONFIG_FILE), 'w') as f:
    yaml.dump(config, f)

# Get the correct audio file based on the new value
audio_file = VALID_KEYS[key]['true_file'] if value else VALID_KEYS[key]['false_file']

# Play the corresponding audio message on all nodes
nodes = config['Asterisk']['Nodes']
for node in nodes:
    subprocess.run(['/usr/sbin/asterisk', '-rx', 'rpt localplay {} {}/SOUNDS/ALERTS/{}'.format(node, SCRIPT_DIR, audio_file.rsplit(".", 1)[0])])