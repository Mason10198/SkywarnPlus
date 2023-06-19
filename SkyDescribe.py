import os
import sys
import requests
import json
from ruamel.yaml import YAML
import urllib.parse
import subprocess
import wave
import contextlib
import re

# Use ruamel.yaml instead of PyYAML
yaml = YAML()

# Directories and Paths
baseDir = os.path.dirname(os.path.realpath(__file__))
configPath = os.path.join(baseDir, "config.yaml")

# Open and read configuration file
with open(configPath, "r") as config_file:
    config = yaml.load(config_file)

# Define tmp_dir
tmp_dir = config.get("DEV", {}).get("TmpDir", "/tmp/SkywarnPlus")

# Path to the data file
data_file = os.path.join(tmp_dir, "data.json")

# Enable debugging
debug = True

def debug_print(*args, **kwargs):
    """
    Print debug information if debugging is enabled.
    """
    if debug:
        print(*args, **kwargs)

def load_state():
    """
    Load the state from the state file if it exists, else return an initial state.

    Returns:
        dict: A dictionary containing data.
    """
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            state = json.load(file)
            return state
    else:
        return {
            "ct": None,
            "id": None,
            "alertscript_alerts": [],
            "last_alerts": [],
            "last_sayalert": [],
            "last_descriptions": {},
        }

import re

def modify_description(description):
    """
    Modify the description to make it more suitable for conversion to audio.

    Args:
        description (str): The description text.

    Returns:
        str: The modified description text.
    """
    # Remove newline characters and replace multiple spaces with a single space
    description = description.replace('\n', ' ')
    description = re.sub(r'\s+', ' ', description)

    # Replace some common weather abbreviations and symbols
    abbreviations = {
        "mph": "miles per hour",
        "knots": "nautical miles per hour",
        "Nm": "nautical miles",
        "nm": "nautical miles",
        "PM": "P.M.",
        "AM": "A.M.",
        "ft.": "feet",
        "in.": "inches",
        "m": "meter",
        "km": "kilometer",
        "mi": "mile",
        "%": "percent",
        "N": "north",
        "S": "south",
        "E": "east",
        "W": "west",
        "NE": "northeast",
        "NW": "northwest",
        "SE": "southeast",
        "SW": "southwest",
        "F": "Fahrenheit",
        "C": "Celsius",
        "UV": "ultraviolet",
        "gusts up to": "gusts of up to",
        "hrs": "hours",
        "hr": "hour",
        "min": "minute",
        "sec": "second",
        "sq": "square",
        "w/": "with",
        "c/o": "care of",
        "blw": "below",
        "abv": "above",
        "avg": "average",
        "fr": "from",
        "to": "to",
        "till": "until",
        "b/w": "between",
        "btwn": "between",
        "N/A": "not available",
        "&": "and",
        "+": "plus",
        "e.g.": "for example",
        "i.e.": "that is",
        "est.": "estimated",
        "...": " dot dot dot ",  # or replace with " pause "
        "\n\n": " pause ",  # or replace with a silence duration
    }
    for abbr, full in abbreviations.items():
        description = description.replace(abbr, full)

    # Space out numerical sequences for better pronunciation
    description = re.sub(r"(\d)", r"\1 ", description)

    # Reform time mentions to a standard format
    description = re.sub(r"(\d{1,2})(\d{2}) (A\.M\.|P\.M\.)", r"\1:\2 \3", description)

    return description.strip()

def convert_to_audio(api_key, text):
    """
    Convert the given text to audio using the Voice RSS Text-to-Speech API.

    Args:
        api_key (str): The API key.
        text (str): The text to convert.

    Returns:
        str: The path to the audio file.
    """
    base_url = 'http://api.voicerss.org/'
    params = {
        'key': api_key,
        'hl': 'en-us',
        'src': urllib.parse.quote(text),
        'c': 'WAV',
        'f': '8khz_8bit_mono'
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()

    audio_file_path = os.path.join(tmp_dir, "description.wav")
    with open(audio_file_path, 'wb') as file:
        file.write(response.content)
    return audio_file_path

def main(index):
    state = load_state()
    alerts = state["last_alerts"]
    descriptions = state["last_descriptions"]
    api_key = config["SkyDescribe"]["APIKey"]

    try:
        alert = alerts[index][0]
        description = descriptions[alert]
    except IndexError:
        print("No alert at index {}".format(index))
        description = "No alert description found at index {}".format(index)

    # Modify the description
    debug_print("Original description:", description)
    description = modify_description(description)
    debug_print("Modified description:", description)

    # Convert description to audio
    audio_file = convert_to_audio(api_key, description)
    
    # Check the length of audio file
    with contextlib.closing(wave.open(audio_file,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    debug_print("Length of the audio file in seconds: ", duration)

    # Play the corresponding audio message on all nodes
    nodes = config["Asterisk"]["Nodes"]
    for node in nodes:
        command = "/usr/sbin/asterisk -rx 'rpt localplay {} {}'".format(
            node, audio_file.rsplit('.', 1)[0]
        )
        debug_print("Running command:", command)
        subprocess.run(command, shell=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: SkyDescribe.py <alert index>")
        sys.exit(1)
    main(int(sys.argv[1]))
