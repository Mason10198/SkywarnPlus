#!/usr/bin/python3

"""
SkyDescribe v0.3.5 by Mason Nelson
==================================================
Text to Speech conversion for Weather Descriptions

This script converts the descriptions of weather alerts to an audio format using 
the VoiceRSS Text-to-Speech API. It first modifies the description to replace 
abbreviations and certain symbols to make the text more suitable for audio conversion.
The script then sends this text to the VoiceRSS API to get the audio data, which 
it saves to a WAV file. Finally, it uses the Asterisk PBX system to play this audio 
file over a radio transmission system.

The script can be run from the command line with an index or a title of an alert as argument.

This file is part of SkywarnPlus.
SkywarnPlus is free software: you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version. SkywarnPlus is distributed in the hope
that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with SkywarnPlus. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import requests
import json
import urllib.parse
import subprocess
import wave
import contextlib
import re
import logging
from ruamel.yaml import YAML
from collections import OrderedDict

# Use ruamel.yaml instead of PyYAML
yaml = YAML()

# Directories and Paths
baseDir = os.path.dirname(os.path.realpath(__file__))
configPath = os.path.join(baseDir, "config.yaml")

# Open and read configuration file
with open(configPath, "r") as config_file:
    config = yaml.load(config_file)

# Define tmp_dir
tmp_dir = config.get("DEV", []).get("TmpDir", "/tmp/SkywarnPlus")

# Define VoiceRSS settings
# get api key, fellback 150
api_key = config.get("SkyDescribe", []).get("APIKey", "")
language = config.get("SkyDescribe", []).get("Language", "en-us")
speed = config.get("SkyDescribe", []).get("Speed", 0)
voice = config.get("SkyDescribe", []).get("Voice", "John")
max_words = config.get("SkyDescribe", []).get("MaxWords", 150)

# Path to the data file
data_file = os.path.join(tmp_dir, "data.json")

# Define logger
logger = logging.getLogger(__name__)
if config.get("Logging", []).get("Debug", False):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Define formatter
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# Define and attach console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Define and attach file handler
log_path = os.path.join(tmp_dir, "SkyDescribe.log")
fh = logging.FileHandler(log_path)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

if not api_key:
    logger.error("SkyDescribe: No VoiceRSS API key found in config.yaml")
    sys.exit(1)


def load_state():
    """
    Load the state from the state file if it exists, else return an initial state.

    Returns:
        OrderedDict: A dictionary containing data.
    """
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            state = json.load(file)
            state["alertscript_alerts"] = state.get("alertscript_alerts", [])
            last_alerts = state.get("last_alerts", [])
            last_alerts = [
                (tuple(x[0]), x[1]) if isinstance(x[0], list) else x
                for x in last_alerts
            ]
            state["last_alerts"] = OrderedDict(last_alerts)
            state["last_sayalert"] = state.get("last_sayalert", [])
            state["active_alerts"] = state.get("active_alerts", [])
            return state
    else:
        return {
            "ct": None,
            "id": None,
            "alertscript_alerts": [],
            "last_alerts": OrderedDict(),
            "last_sayalert": [],
            "active_alerts": [],
        }


def modify_description(description):
    """
    Modify the description to make it more suitable for conversion to audio.

    Args:
        description (str): The description text.
        alert_title (str): The title of the alert.

    Returns:
        str: The modified description text.
    """
    # Remove newline characters and replace multiple spaces with a single space
    description = description.replace("\n", " ")
    description = re.sub(r"\s+", " ", description)

    # Replace some common weather abbreviations and symbols
    abbreviations = {
        r"\bmph\b": "miles per hour",
        r"\bknots\b": "nautical miles per hour",
        r"\bNm\b": "nautical miles",
        r"\bnm\b": "nautical miles",
        r"\bft\.\b": "feet",
        r"\bin\.\b": "inches",
        r"\bm\b": "meter",
        r"\bkm\b": "kilometer",
        r"\bmi\b": "mile",
        r"\b%\b": "percent",
        r"\bN\b": "north",
        r"\bS\b": "south",
        r"\bE\b": "east",
        r"\bW\b": "west",
        r"\bNE\b": "northeast",
        r"\bNW\b": "northwest",
        r"\bSE\b": "southeast",
        r"\bSW\b": "southwest",
        r"\bF\b": "Fahrenheit",
        r"\bC\b": "Celsius",
        r"\bUV\b": "ultraviolet",
        r"\bgusts up to\b": "gusts of up to",
        r"\bhrs\b": "hours",
        r"\bhr\b": "hour",
        r"\bmin\b": "minute",
        r"\bsec\b": "second",
        r"\bsq\b": "square",
        r"\bw/\b": "with",
        r"\bc/o\b": "care of",
        r"\bblw\b": "below",
        r"\babv\b": "above",
        r"\bavg\b": "average",
        r"\bfr\b": "from",
        r"\bto\b": "to",
        r"\btill\b": "until",
        r"\bb/w\b": "between",
        r"\bbtwn\b": "between",
        r"\bN/A\b": "not available",
        r"\b&\b": "and",
        r"\b\+\b": "plus",
        r"\be\.g\.\b": "for example",
        r"\bi\.e\.\b": "that is",
        r"\best\.\b": "estimated",
        r"\b\.\.\.\b": ".",
        r"\b\n\n\b": ".",
        r"\b\n\b": ".",
        r"\bEDT\b": "eastern daylight time",
        r"\bEST\b": "eastern standard time",
        r"\bCST\b": "central standard time",
        r"\bCDT\b": "central daylight time",
        r"\bMST\b": "mountain standard time",
        r"\bMDT\b": "mountain daylight time",
        r"\bPST\b": "pacific standard time",
        r"\bPDT\b": "pacific daylight time",
        r"\bAKST\b": "Alaska standard time",
        r"\bAKDT\b": "Alaska daylight time",
        r"\bHST\b": "Hawaii standard time",
        r"\bHDT\b": "Hawaii daylight time",
    }
    for abbr, full in abbreviations.items():
        description = re.sub(abbr, full, description)

    # Remove '*' characters
    description = description.replace("*", "")

    # Replace '  ' with a single space
    description = re.sub(r"\s\s+", " ", description)

    # Replace '. . . ' with a single space. The \s* takes care of any number of spaces.
    description = re.sub(r"\.\s*\.\s*\.\s*", " ", description)

    # Correctly format time mentions in 12-hour format (add colon) and avoid adding spaces in these
    description = re.sub(r"(\b\d{1,2})(\d{2}\s*[AP]M)", r"\1:\2", description)

    # Remove spaces between numbers and "pm" or "am"
    description = re.sub(r"(\d) (\s*[AP]M)", r"\1\2", description)

    # Only separate numerical sequences followed by a letter, and avoid adding spaces in multi-digit numbers
    description = re.sub(r"(\d)(?=[A-Za-z])", r"\1 ", description)

    # Replace any remaining ... with a single period
    description = re.sub(r"\.\s*", ". ", description).strip()

    # Limit the description to a maximum number of words
    words = description.split()
    logger.debug("SkyDescribe: Description has %d words.", len(words))
    if len(words) > max_words:
        description = " ".join(words[:max_words])
        logger.info("SkyDescribe: Description has been limited to %d words.", max_words)

    return description


def convert_to_audio(api_key, text):
    """
    Convert the given text to audio using the Voice RSS Text-to-Speech API.

    Args:
        api_key (str): The API key.
        text (str): The text to convert.

    Returns:
        str: The path to the audio file.
    """
    base_url = "http://api.voicerss.org/"
    params = {
        "key": api_key,
        "hl": str(language),
        "src": text,
        "c": "WAV",
        "f": "8khz_16bit_mono",
        "r": str(speed),
        "v": str(voice),
    }

    logger.debug(
        "SkyDescribe: Voice RSS API URL: %s",
        base_url + "?" + urllib.parse.urlencode(params),
    )

    response = requests.get(base_url, params=params)
    response.raise_for_status()

    audio_file_path = os.path.join(tmp_dir, "describe.wav")
    with open(audio_file_path, "wb") as file:
        file.write(response.content)
    return audio_file_path


def main(index_or_title):
    state = load_state()
    alerts = list(state["last_alerts"].items())

    # Determine if the argument is an index or a title
    if str(index_or_title).isdigit():
        index = int(index_or_title) - 1
        if index >= len(alerts):
            logger.error("SkyDescribe: No alert found at index %d.", index + 1)
            description = "Sky Describe error, no alert found at index {}.".format(
                index + 1
            )
        else:
            alert, alert_data = alerts[index]
            (_, description, _) = alert_data
    else:
        # Argument is not an index, assume it's a title
        title = index_or_title
        for alert, alert_data in alerts:
            if alert == title:  # Assuming alert is a title
                _, description, _ = alert_data
                break
        else:
            logger.error("SkyDescribe: No alert with title %s found.", title)
            description = "Sky Describe error, no alert found with title {}.".format(
                title
            )

    logger.debug("\n\nSkyDescribe: Original description: %s", description)

    # If the description is not an error message, extract the alert title
    if not "Sky Describe error" in description:
        alert_title = alert  # As alert itself is the title now
        logger.info("SkyDescribe: Generating description for alert: %s", alert_title)
        # Add the alert title at the beginning
        description = "Detailed alert information for {}. {}".format(
            alert_title, description
        )
        description = modify_description(description)

    logger.debug("\n\nSkyDescribe: Modified description: %s\n\n", description)

    audio_file = convert_to_audio(api_key, description)

    with contextlib.closing(wave.open(audio_file, "r")) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    logger.debug("SkyDescribe: Length of the audio file in seconds: %s", duration)

    nodes = config["Asterisk"]["Nodes"]
    for node in nodes:
        logger.info("SkyDescribe: Broadcasting description on node %s.", node)
        command = "/usr/sbin/asterisk -rx 'rpt localplay {} {}'".format(
            node, audio_file.rsplit(".", 1)[0]
        )
        logger.debug("SkyDescribe: Running command: %s", command)
        subprocess.run(command, shell=True)


# Script entry point
if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: SkyDescribe.py <alert index or title>")
        sys.exit(1)
    main(sys.argv[1])
