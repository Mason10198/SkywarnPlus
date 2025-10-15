#!/usr/bin/python3

"""
CountyIDGen.py by Mason Nelson
===============================================================================
This script is a utility for generating WAV audio files corresponding to each 
county code defined in the SkywarnPlus config.yaml. The audio files are generated 
using the Voice RSS Text-to-Speech API and the settings defined in the config.yaml.

This script will generate the files, save them in the correct location, and automatically
modify the SkywarnPlus config.yaml to utilize them.

This file is part of SkywarnPlus.
SkywarnPlus is free software: you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version. SkywarnPlus is distributed in the hope
that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with SkywarnPlus. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import io
import re
import sys
import requests
import logging
import zipfile
from datetime import datetime
from functools import lru_cache

# Lazy imports for performance
def _lazy_import_yaml():
    """Lazy import YAML to avoid loading unless needed."""
    try:
        from ruamel.yaml import YAML
        return YAML()
    except ImportError:
        raise ImportError("ruamel.yaml is required")

def _lazy_import_pydub():
    """Lazy import pydub to avoid loading unless needed."""
    try:
        from pydub import AudioSegment
        from pydub.silence import split_on_silence
        return AudioSegment, split_on_silence
    except ImportError:
        raise ImportError("pydub is required for audio processing")

# Initialize YAML
yaml = _lazy_import_yaml()

# Directories and Paths
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
COUNTY_CODES_PATH = os.path.join(BASE_DIR, "CountyCodes.md")

# Optimized configuration loading with caching
@lru_cache(maxsize=1)
def _load_config():
    """Load configuration with caching."""
    with open(CONFIG_PATH, "r") as config_file:
        return yaml.load(config_file)

# Load configurations
config = _load_config()

# Logging setup
LOG_CONFIG = config.get("Logging", {})
ENABLE_DEBUG = LOG_CONFIG.get("Debug", False)
LOG_FILE = LOG_CONFIG.get("LogPath", os.path.join(BASE_DIR, "SkywarnPlus.log"))

# Set up logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG if ENABLE_DEBUG else logging.INFO)

# Set up log message formatting
LOG_FORMATTER = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# Set up console log handler
C_HANDLER = logging.StreamHandler()
C_HANDLER.setFormatter(LOG_FORMATTER)
LOGGER.addHandler(C_HANDLER)

# Ensure the directory for the log file exists
log_directory = os.path.dirname(LOG_FILE)
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Set up file log handler
F_HANDLER = logging.FileHandler(LOG_FILE)
F_HANDLER.setFormatter(LOG_FORMATTER)
LOGGER.addHandler(F_HANDLER)

# Extract API parameters from the config
API_KEY = config["SkyDescribe"]["APIKey"]
LANGUAGE = config["SkyDescribe"]["Language"]
SPEED = str(config["SkyDescribe"]["Speed"])
VOICE = config["SkyDescribe"]["Voice"]
SOUNDS_PATH = config.get("Alerting", {}).get(
    "SoundsPath", os.path.join(BASE_DIR, "SOUNDS")
)


def generate_wav(api_key, language, speed, voice, text, output_file):
    """
    Convert the given text to audio using the Voice RSS Text-to-Speech API and trims silence.
    """
    base_url = "http://api.voicerss.org/"
    params = {
        "key": api_key,
        "hl": language,
        "src": text,
        "c": "WAV",
        "f": "8khz_16bit_mono",
        "r": str(speed),
        "v": voice,
    }

    # Use session for connection pooling
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'SkywarnPlus-CountyIDGen/0.8.0',
        'Accept': 'audio/wav',
        'Accept-Encoding': 'gzip, deflate'
    })
    
    response = session.get(base_url, params=params, timeout=30)
    response.raise_for_status()

    # If the response text contains "ERROR" then log it and exit
    if "ERROR" in response.text:
        LOGGER.error("SkyDescribe: %s", response.text)
        sys.exit(1)

    # Load the audio data into pydub's AudioSegment
    sound = AudioSegment.from_wav(io.BytesIO(response.content))

    # Normalize the entire audio clip
    target_dBFS = -6.0
    gain_difference = target_dBFS - sound.max_dBFS
    sound = sound.apply_gain(gain_difference)

    # Split track where silence is 100ms or more and get chunks
    chunks = split_on_silence(sound, min_silence_len=200, silence_thresh=-40)

    # If there are chunks, concatenate all of them
    if chunks:
        combined_sound = sum(chunks, AudioSegment.empty())

        # Export the combined audio
        combined_sound.export(output_file, format="wav")
    else:
        # If there are no chunks, just save the original audio
        sound.export(output_file, format="wav")


def sanitize_text_for_tts(text):
    """
    Sanitize the text for TTS processing.
    Remove characters that aren't alphanumeric or whitespace.
    """
    sanitized_text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return sanitized_text


def backup_existing_files(path, filename_pattern, backup_name):
    """
    Backup files matching the filename pattern in the specified path to a zip file.
    """
    files_to_backup = [
        f
        for f in os.listdir(path)
        if f.startswith(filename_pattern) and f.endswith(".wav")
    ]
    if not files_to_backup:
        return

    with zipfile.ZipFile(backup_name, "w") as zipf:
        for file in files_to_backup:
            zipf.write(os.path.join(path, file), file)


def process_county_codes():
    """
    Process county codes and make changes.
    """
    new_county_codes = []
    for entry in config["Alerting"]["CountyCodes"]:
        overwrite = False
        if isinstance(entry, str):  # County code without WAV file
            county_code = entry
        elif isinstance(entry, dict):  # County code with WAV file
            county_code = list(entry.keys())[0]

            county_name = county_data.get(county_code)
            sanitized_county_name = sanitize_text_for_tts(county_name)
            expected_wav_file = "{}.wav".format(sanitized_county_name)

            if os.path.exists(os.path.join(SOUNDS_PATH, expected_wav_file)):
                if not overwrite:
                    user_input = input(
                        "The WAV file for {} ({}) already exists. Do you want to overwrite it? [yes/no]: ".format(
                            county_name, expected_wav_file
                        )
                    ).lower()
                    if user_input != "yes":
                        LOGGER.info(
                            "Skipping generation for {} due to user input.".format(
                                county_name
                            )
                        )
                        new_county_codes.append({county_code: expected_wav_file})
                        continue  # Skip to the next county code
                    overwrite = True

        # At this point, we are sure that we either have a new county code or the user has agreed to overwrite.
        county_name = county_data.get(county_code)
        if county_name:
            sanitized_county_name = sanitize_text_for_tts(county_name)
            output_file = os.path.join(
                SOUNDS_PATH, "{}.wav".format(sanitized_county_name)
            )
            generate_wav(
                API_KEY, LANGUAGE, SPEED, VOICE, sanitized_county_name, output_file
            )

            # Add the mapping for the county code to the new list
            new_county_codes.append(
                {county_code: "{}.wav".format(sanitized_county_name)}
            )

    # Replace the old CountyCodes list with the new one
    config["Alerting"]["CountyCodes"] = new_county_codes


def load_county_codes_from_md(md_file_path):
    """
    Load county names from the MD file and return a dictionary mapping county codes to county names.
    """
    with open(md_file_path, "r") as file:
        lines = file.readlines()

    county_data = {}
    for line in lines:
        if line.startswith("|") and "County Name" not in line and "-----" not in line:
            _, county_name, code, _ = line.strip().split("|")
            county_data[code.strip()] = county_name.strip()

    return county_data


def display_initial_warning():
    warning_message = """
    ============================================================
    WARNING: Please read the following information carefully before proceeding.

    This utility is designed to generate WAV audio files corresponding to each county code 
    defined in the SkywarnPlus config.yaml using the Voice RSS Text-to-Speech API. The generated 
    audio files will be saved in the appropriate location, and the SkywarnPlus config.yaml will 
    be automatically updated to use them.

    However, a few things to keep in mind:
    - The script will only attempt to generate WAV files for county codes that are defined in the config.
    
    - Pronunciations for some county names might not be accurate. In such cases, you may need to 
      manually create the files using VoiceRSS. This might involve intentionally misspelling the county 
      name to achieve the desired pronunciation.
    
    - This script will attempt to backup any files before it modifies them, but it is always a good idea to
      manually back up your existing configuration and files before running this script.

    - This script will modify your config.yaml file, so you should ALWAYS double check the changes it makes.
      There might be improperly formatted indentations, comments, etc. that you will need to fix manually.

    Proceed with caution.
    ============================================================
    """
    print(warning_message)


# Display the initial warning
display_initial_warning()

# Wait for user acknowledgment before proceeding.
user_input = input("Do you want to proceed? [yes/no]: ").lower()
if user_input != "yes":
    LOGGER.info("Aborting process due to user input.")
    sys.exit()

# Load county names and generate WAV files
backup_date = datetime.now().strftime("%Y%m%d")
backup_name = os.path.join(SOUNDS_PATH, "CountyID_Backup_{}.zip".format(backup_date))
backup_existing_files(SOUNDS_PATH, "", backup_name)

# Load county codes and names
county_data = load_county_codes_from_md(COUNTY_CODES_PATH)

# Call the function to process the county codes
process_county_codes()

# Update config.yaml to reflect the WAV file mappings
for i, county_code in enumerate(config["Alerting"]["CountyCodes"]):
    if isinstance(county_code, str):
        county_name = county_data.get(county_code)
        if county_name:
            sanitized_county_name = sanitize_text_for_tts(county_name)
            config["Alerting"]["CountyCodes"][i] = {
                county_code: "{}.wav".format(sanitized_county_name)
            }

# Write the updated config.yaml
with open(CONFIG_PATH, "w") as config_file:
    yaml.indent(sequence=4, offset=2)
    yaml.dump(config, config_file)

LOGGER.info("County WAV files generation completed.")
