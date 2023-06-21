#!/usr/bin/python3

"""
SkywarnPlus v0.2.4 by Mason Nelson (N5LSN/WRKF394)
==================================================
SkywarnPlus is a utility that retrieves severe weather alerts from the National 
Weather Service and integrates these alerts with an Asterisk/app_rpt based 
radio repeater controller. 

This utility is designed to be highly configurable, allowing users to specify 
particular counties for which to check for alerts, the types of alerts to include 
or block, and how these alerts are integrated into their radio repeater system. 

This includes features such as automatic voice alerts and a tail message feature 
for constant updates. All alerts are sorted by severity and cover a broad range 
of weather conditions such as hurricane warnings, thunderstorms, heat waves, etc. 

Configurable through a .ini file, SkywarnPlus serves as a comprehensive and 
flexible tool for those who need to stay informed about weather conditions 
and disseminate this information through their radio repeater system.
"""

import os
import json
import logging
import requests
import shutil
import fnmatch
import subprocess
import time
import wave
import contextlib
import math
from datetime import datetime, timezone
from dateutil import parser
from pydub import AudioSegment
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
    config = json.loads(json.dumps(config))  # Convert config to a normal dictionary

# Check if SkywarnPlus is enabled
master_enable = config.get("SKYWARNPLUS", {}).get("Enable", False)
if not master_enable:
    print("SkywarnPlus is disabled in config.yaml, exiting...")
    exit()

# Define tmp_dir and sounds_path
tmp_dir = config.get("DEV", {}).get("TmpDir", "/tmp/SkywarnPlus")
sounds_path = config.get("Alerting", {}).get(
    "SoundsPath", os.path.join(baseDir, "SOUNDS")
)

# Define countyCodes
countyCodes = config.get("Alerting", {}).get("CountyCodes", [])

# Create tmp_dir if it doesn't exist
if tmp_dir:
    os.makedirs(tmp_dir, exist_ok=True)
else:
    print("Error: tmp_dir is not set.")

# Define Blocked events
global_blocked_events = config.get("Blocking", {}).get("GlobalBlockedEvents", [])
if global_blocked_events is None:
    global_blocked_events = []
sayalert_blocked_events = config.get("Blocking", {}).get("SayAlertBlockedEvents", [])
if sayalert_blocked_events is None:
    sayalert_blocked_events = []
tailmessage_blocked_events = config.get("Blocking", {}).get(
    "TailmessageBlockedEvents", []
)
if tailmessage_blocked_events is None:
    tailmessage_blocked_events = []

# Define Max Alerts
max_alerts = config.get("Alerting", {}).get("MaxAlerts", 99)

# Define Tailmessage configuration
tailmessage_config = config.get("Tailmessage", {})
enable_tailmessage = tailmessage_config.get("Enable", False)
tailmessage_file = tailmessage_config.get(
    "TailmessagePath", os.path.join(tmp_dir, "wx-tail.wav")
)

# Define IDChange configuration
idchange_config = config.get("IDChange", {})
enable_idchange = idchange_config.get("Enable", False)

# Data file path
data_file = os.path.join(tmp_dir, "data.json")

# Define possible alert strings
WS = [
    "911 Telephone Outage Emergency",
    "Administrative Message",
    "Air Quality Alert",
    "Air Stagnation Advisory",
    "Arroyo And Small Stream Flood Advisory",
    "Ashfall Advisory",
    "Ashfall Warning",
    "Avalanche Advisory",
    "Avalanche Warning",
    "Avalanche Watch",
    "Beach Hazards Statement",
    "Blizzard Warning",
    "Blizzard Watch",
    "Blowing Dust Advisory",
    "Blowing Dust Warning",
    "Brisk Wind Advisory",
    "Child Abduction Emergency",
    "Civil Danger Warning",
    "Civil Emergency Message",
    "Coastal Flood Advisory",
    "Coastal Flood Statement",
    "Coastal Flood Warning",
    "Coastal Flood Watch",
    "Dense Fog Advisory",
    "Dense Smoke Advisory",
    "Dust Advisory",
    "Dust Storm Warning",
    "Earthquake Warning",
    "Evacuation - Immediate",
    "Excessive Heat Warning",
    "Excessive Heat Watch",
    "Extreme Cold Warning",
    "Extreme Cold Watch",
    "Extreme Fire Danger",
    "Extreme Wind Warning",
    "Fire Warning",
    "Fire Weather Watch",
    "Flash Flood Statement",
    "Flash Flood Warning",
    "Flash Flood Watch",
    "Flood Advisory",
    "Flood Statement",
    "Flood Warning",
    "Flood Watch",
    "Freeze Warning",
    "Freeze Watch",
    "Freezing Fog Advisory",
    "Freezing Rain Advisory",
    "Freezing Spray Advisory",
    "Frost Advisory",
    "Gale Warning",
    "Gale Watch",
    "Hard Freeze Warning",
    "Hard Freeze Watch",
    "Hazardous Materials Warning",
    "Hazardous Seas Warning",
    "Hazardous Seas Watch",
    "Hazardous Weather Outlook",
    "Heat Advisory",
    "Heavy Freezing Spray Warning",
    "Heavy Freezing Spray Watch",
    "High Surf Advisory",
    "High Surf Warning",
    "High Wind Warning",
    "High Wind Watch",
    "Hurricane Force Wind Warning",
    "Hurricane Force Wind Watch",
    "Hurricane Local Statement",
    "Hurricane Warning",
    "Hurricane Watch",
    "Hydrologic Advisory",
    "Hydrologic Outlook",
    "Ice Storm Warning",
    "Lake Effect Snow Advisory",
    "Lake Effect Snow Warning",
    "Lake Effect Snow Watch",
    "Lake Wind Advisory",
    "Lakeshore Flood Advisory",
    "Lakeshore Flood Statement",
    "Lakeshore Flood Warning",
    "Lakeshore Flood Watch",
    "Law Enforcement Warning",
    "Local Area Emergency",
    "Low Water Advisory",
    "Marine Weather Statement",
    "Nuclear Power Plant Warning",
    "Radiological Hazard Warning",
    "Red Flag Warning",
    "Rip Current Statement",
    "Severe Thunderstorm Warning",
    "Severe Thunderstorm Watch",
    "Severe Weather Statement",
    "Shelter In Place Warning",
    "Short Term Forecast",
    "Small Craft Advisory",
    "Small Craft Advisory For Hazardous Seas",
    "Small Craft Advisory For Rough Bar",
    "Small Craft Advisory For Winds",
    "Small Stream Flood Advisory",
    "Snow Squall Warning",
    "Special Marine Warning",
    "Special Weather Statement",
    "Storm Surge Warning",
    "Storm Surge Watch",
    "Storm Warning",
    "Storm Watch",
    "Test",
    "Tornado Warning",
    "Tornado Watch",
    "Tropical Depression Local Statement",
    "Tropical Storm Local Statement",
    "Tropical Storm Warning",
    "Tropical Storm Watch",
    "Tsunami Advisory",
    "Tsunami Warning",
    "Tsunami Watch",
    "Typhoon Local Statement",
    "Typhoon Warning",
    "Typhoon Watch",
    "Urban And Small Stream Flood Advisory",
    "Volcano Warning",
    "Wind Advisory",
    "Wind Chill Advisory",
    "Wind Chill Warning",
    "Wind Chill Watch",
    "Winter Storm Warning",
    "Winter Storm Watch",
    "Winter Weather Advisory",
]

# Generate the WA list based on the length of WS
WA = [str(i + 1) for i in range(len(WS))]

# Test if the script needs to start from a clean slate
CLEANSLATE = config.get("DEV", {}).get("CLEANSLATE", False)
if CLEANSLATE:
    shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)

# Logging setup
log_config = config.get("Logging", {})
enable_debug = log_config.get("Debug", False)
log_file = log_config.get("LogPath", os.path.join(tmp_dir, "SkywarnPlus.log"))

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if enable_debug else logging.INFO)

# Set up log message formatting
log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# Set up console log handler
c_handler = logging.StreamHandler()
c_handler.setFormatter(log_formatter)
logger.addHandler(c_handler)

# Set up file log handler
f_handler = logging.FileHandler(log_file)
f_handler.setFormatter(log_formatter)
logger.addHandler(f_handler)

# Log some debugging information
logger.debug("Base directory: %s", baseDir)
logger.debug("Temporary directory: %s", tmp_dir)
logger.debug("Sounds path: %s", sounds_path)
logger.debug("Tailmessage path: %s", tailmessage_file)
logger.debug("Global Blocked events: %s", global_blocked_events)
logger.debug("SayAlert Blocked events: %s", sayalert_blocked_events)
logger.debug("Tailmessage Blocked events: %s", tailmessage_blocked_events)


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


def save_state(state):
    """
    Save the state to the state file.

    Args:
        state (OrderedDict): A dictionary containing data.
    """
    state["alertscript_alerts"] = list(state["alertscript_alerts"])
    state["last_alerts"] = list(state["last_alerts"].items())
    state["last_sayalert"] = list(state["last_sayalert"])
    state["active_alerts"] = list(state["active_alerts"])
    with open(data_file, "w") as file:
        json.dump(state, file, ensure_ascii=False, indent=4)


def getAlerts(countyCodes):
    """
    Retrieve severe weather alerts for specified county codes.

    Args:
        countyCodes (list): List of county codes.

    Returns:
        alerts (list): List of active weather alerts.
        descriptions (dict): Dictionary of alert descriptions.
    """
    # Mapping for severity for API response and the 'words' severity
    severity_mapping_api = {
        "Extreme": 4,
        "Severe": 3,
        "Moderate": 2,
        "Minor": 1,
        "Unknown": 0,
    }
    severity_mapping_words = {"Warning": 4, "Watch": 3, "Advisory": 2, "Statement": 1}

    alerts = OrderedDict()
    seen_alerts = set()  # Store seen alerts
    current_time = datetime.now(timezone.utc)
    logger.debug("getAlerts: Current time: %s", current_time)

    # Check if injection is enabled
    if config.get("DEV", {}).get("INJECT", False):
        logger.debug("getAlerts: DEV Alert Injection Enabled")
        injected_alerts = config["DEV"].get("INJECTALERTS", [])
        logger.debug("getAlerts: Injecting alerts: %s", injected_alerts)

        for event in injected_alerts:
            last_word = event.split()[-1]
            severity = severity_mapping_words.get(last_word, 0)
            alerts[(event, severity)] = "Manually injected."

        alerts = OrderedDict(list(alerts.items())[:max_alerts])

        return alerts

    for countyCode in countyCodes:
        url = "https://api.weather.gov/alerts/active?zone={}".format(countyCode)
        logger.debug("getAlerts: Checking for alerts in %s at URL: %s", countyCode, url)
        response = requests.get(url)

        if response.status_code == 200:
            alert_data = response.json()
            for feature in alert_data["features"]:
                onset = feature["properties"].get("onset")
                ends = feature["properties"].get("ends")
                if onset and ends:
                    onset_time = parser.isoparse(onset)
                    ends_time = parser.isoparse(ends)
                    # Convert alert times to UTC
                    onset_time_utc = onset_time.astimezone(timezone.utc)
                    ends_time_utc = ends_time.astimezone(timezone.utc)
                    if onset_time_utc <= current_time < ends_time_utc:
                        event = feature["properties"]["event"]
                        description = feature["properties"].get("description", "")
                        severity = feature["properties"].get("severity", None)
                        # Check if alert has already been seen
                        if event in seen_alerts:
                            continue

                        # Initialize a flag to check if the event is globally blocked
                        is_blocked = False
                        for global_blocked_event in global_blocked_events:
                            if fnmatch.fnmatch(event, global_blocked_event):
                                logger.debug(
                                    "getAlerts: Globally Blocking %s as per configuration",
                                    event,
                                )
                                is_blocked = True
                                break

                        # Skip to the next feature if the event is globally blocked
                        if is_blocked:
                            continue

                        if severity is None:
                            last_word = event.split()[-1]
                            severity = severity_mapping_words.get(last_word, 0)
                        else:
                            severity = severity_mapping_api.get(severity, 0)
                        alerts[(event, severity)] = description
                        seen_alerts.add(event)
                    else:
                        logger.debug(
                            "getAlerts: Skipping alert %s, not active.", event
                        )
                        logger.debug("Current time: %s | Alert onset: %s | Alert ends %s", current_time, onset_time_utc, ends_time_utc)

        else:
            logger.error(
                "Failed to retrieve alerts for %s, HTTP status code %s, response: %s",
                countyCode,
                response.status_code,
                response.text,
            )

    alerts = OrderedDict(
        sorted(
            alerts.items(),
            key=lambda item: (
                item[0][1],  # API-provided severity
                severity_mapping_words.get(item[0][0].split()[-1], 0),  # Words severity
            ),
            reverse=True,
        )
    )

    alerts = OrderedDict(list(alerts.items())[:max_alerts])

    return alerts


def sayAlert(alerts):
    """
    Generate and broadcast severe weather alert sounds on Asterisk.

    Args:
        alerts (OrderedDict): OrderedDict of active weather alerts and their descriptions.
    """
    # Define the path of the alert file
    state = load_state()

    # Extract only the alert names from the OrderedDict keys
    alert_names = [alert[0] for alert in alerts.keys()]

    filtered_alerts = []
    for alert in alert_names:
        if any(
            fnmatch.fnmatch(alert, blocked_event)
            for blocked_event in sayalert_blocked_events
        ):
            logger.debug("sayAlert: blocking %s as per configuration", alert)
            continue
        filtered_alerts.append(alert)

    # Check if the filtered alerts are the same as the last run
    if filtered_alerts == state["last_sayalert"]:
        logger.debug(
            "sayAlert: The filtered alerts are the same as the last run. Not broadcasting."
        )
        return

    state["last_sayalert"] = filtered_alerts
    save_state(state)

    alert_file = "{}/alert.wav".format(tmp_dir)

    combined_sound = AudioSegment.from_wav(
        os.path.join(sounds_path, "ALERTS", "SWP_149.wav")
    )
    sound_effect = AudioSegment.from_wav(
        os.path.join(sounds_path, "ALERTS", "SWP_147.wav")
    )

    alert_count = 0
    for alert in filtered_alerts:
        try:
            index = WS.index(alert)
            audio_file = AudioSegment.from_wav(
                os.path.join(sounds_path, "ALERTS", "SWP_{}.wav".format(WA[index]))
            )
            combined_sound += sound_effect + audio_file
            logger.debug(
                "sayAlert: Added %s (SWP_%s.wav) to alert sound", alert, WA[index]
            )
            alert_count += 1
        except ValueError:
            logger.error("sayAlert: Alert not found: %s", alert)
        except FileNotFoundError:
            logger.error(
                "sayAlert: Audio file not found: %s/ALERTS/SWP_%s.wav",
                sounds_path,
                WA[index],
            )

    if alert_count == 0:
        logger.debug("sayAlert: All alerts were blocked, not broadcasting any alerts.")
        return

    logger.debug("sayAlert: Exporting alert sound to %s", alert_file)
    converted_combined_sound = convertAudio(combined_sound)
    converted_combined_sound.export(alert_file, format="wav")

    logger.debug("sayAlert: Replacing tailmessage with silence")
    silence = AudioSegment.silent(duration=100)
    converted_silence = convertAudio(silence)
    converted_silence.export(tailmessage_file, format="wav")

    node_numbers = config.get("Asterisk", {}).get("Nodes", [])
    for node_number in node_numbers:
        logger.info("Broadcasting alert on node %s", node_number)
        command = '/usr/sbin/asterisk -rx "rpt localplay {} {}"'.format(
            node_number, os.path.splitext(os.path.abspath(alert_file))[0]
        )
        subprocess.run(command, shell=True)

    # Get the duration of the alert_file
    with contextlib.closing(wave.open(alert_file, "r")) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = math.ceil(frames / float(rate))

    wait_time = duration + 5

    logger.info(
        "Waiting %s seconds for Asterisk to make announcement to avoid doubling alerts with tailmessage...",
        wait_time,
    )
    time.sleep(wait_time)


def sayAllClear():
    """
    Generate and broadcast 'all clear' message on Asterisk.
    """
    # Empty the last_sayalert list so that the next run will broadcast alerts
    state = load_state()
    state["last_sayalert"] = []
    save_state(state)

    alert_clear = os.path.join(sounds_path, "ALERTS", "SWP_148.wav")

    node_numbers = config.get("Asterisk", {}).get("Nodes", [])
    for node_number in node_numbers:
        logger.info("Broadcasting all clear message on node %s", node_number)
        command = '/usr/sbin/asterisk -rx "rpt localplay {} {}"'.format(
            node_number, os.path.splitext(os.path.abspath(alert_clear))[0]
        )
        subprocess.run(command, shell=True)


def buildTailmessage(alerts):
    """
    Build a tailmessage, which is a short message appended to the end of a
    transmission to update on the weather conditions.

    Args:
        alerts (list): List of active weather alerts.
    """

    # Extract only the alert names from the OrderedDict keys
    alert_names = [alert[0] for alert in alerts.keys()]

    if not alerts:
        logger.info("buildTailMessage: No alerts, creating silent tailmessage")
        silence = AudioSegment.silent(duration=100)
        converted_silence = convertAudio(silence)
        converted_silence.export(tailmessage_file, format="wav")
        return

    combined_sound = AudioSegment.empty()
    sound_effect = AudioSegment.from_wav(
        os.path.join(sounds_path, "ALERTS", "SWP_147.wav")
    )

    for alert in alert_names:
        if any(
            fnmatch.fnmatch(alert, blocked_event)
            for blocked_event in tailmessage_blocked_events
        ):
            logger.debug(
                "buildTailMessage: Alert blocked by TailmessageBlockedEvents: %s", alert
            )
            continue

        try:
            index = WS.index(alert)
            audio_file = AudioSegment.from_wav(
                os.path.join(sounds_path, "ALERTS", "SWP_{}.wav".format(WA[index]))
            )
            combined_sound += sound_effect + audio_file
            logger.debug(
                "buildTailMessage: Added %s (SWP_%s.wav) to tailmessage",
                alert,
                WA[index],
            )
        except ValueError:
            logger.error("Alert not found: %s", alert)
        except FileNotFoundError:
            logger.error(
                "Audio file not found: %s/ALERTS/SWP_%s.wav",
                sounds_path,
                WA[index],
            )

    if combined_sound.empty():
        logger.debug(
            "buildTailMessage: All alerts were blocked, creating silent tailmessage"
        )
        combined_sound = AudioSegment.silent(duration=100)

    logger.info("Built new tailmessage")
    logger.debug("buildTailMessage: Exporting tailmessage to %s", tailmessage_file)
    converted_combined_sound = convertAudio(combined_sound)
    converted_combined_sound.export(tailmessage_file, format="wav")


def changeCT(ct):
    """
    Change the current Courtesy Tone (CT) to the one specified.

    This function first checks if the specified CT is already in use. If so, it does not make any changes.
    If the CT needs to be changed, it replaces the current CT files with the new ones and updates the state file.

    Args:
        ct (str): The name of the new CT to use. This should be one of the CTs specified in the config file.

    Returns:
        bool: True if the CT was changed, False otherwise.

    Raises:
        FileNotFoundError: If the specified CT files are not found.
    """
    state = load_state()
    current_ct = state["ct"]
    tone_dir = config["CourtesyTones"].get(
        "ToneDir", os.path.join(sounds_path, "TONES")
    )
    ct1 = config["CourtesyTones"]["Tones"]["CT1"]
    ct2 = config["CourtesyTones"]["Tones"]["CT2"]
    wx_ct = config["CourtesyTones"]["Tones"]["WXCT"]
    rpt_ct1 = config["CourtesyTones"]["Tones"]["RptCT1"]
    rpt_ct2 = config["CourtesyTones"]["Tones"]["RptCT2"]

    logger.debug("changeCT: Tone directory: %s", tone_dir)
    logger.debug("changeCT: Local CT: %s", ct1)
    logger.debug("changeCT: Link CT: %s", ct2)
    logger.debug("changeCT: WX CT: %s", wx_ct)
    logger.debug("changeCT: Rpt Local CT: %s", rpt_ct1)
    logger.debug("changeCT: Rpt Link CT: %s", rpt_ct2)
    logger.debug("changeCT: CT argument: %s", ct)

    if not ct:
        logger.error("changeCT: called with no CT specified")
        return

    current_ct = None
    if state:
        current_ct = state["ct"]

    logger.debug("changeCT: Current CT - %s", current_ct)

    if ct == current_ct:
        logger.debug("changeCT: Courtesy tones are already %s, no changes made.", ct)
        return False

    if ct == "NORMAL":
        logger.info("Changing to NORMAL courtesy tones")
        src_file = os.path.join(tone_dir, ct1)
        dest_file = os.path.join(tone_dir, rpt_ct1)
        logger.debug("changeCT: Copying %s to %s", src_file, dest_file)
        shutil.copyfile(src_file, dest_file)

        src_file = os.path.join(tone_dir, ct2)
        dest_file = os.path.join(tone_dir, rpt_ct2)
        logger.debug("changeCT: Copying %s to %s", src_file, dest_file)
        shutil.copyfile(src_file, dest_file)
    else:
        logger.info("Changing to %s courtesy tone", ct)
        src_file = os.path.join(tone_dir, wx_ct)
        dest_file = os.path.join(tone_dir, rpt_ct1)
        logger.debug("changeCT: Copying %s to %s", src_file, dest_file)
        shutil.copyfile(src_file, dest_file)

        src_file = os.path.join(tone_dir, wx_ct)
        dest_file = os.path.join(tone_dir, rpt_ct2)
        logger.debug("changeCT: Copying %s to %s", src_file, dest_file)
        shutil.copyfile(src_file, dest_file)

    state["ct"] = ct
    save_state(state)

    return True


def changeID(id):
    """
    Change the current Identifier (ID) to the one specified.

    This function first checks if the specified ID is already in use. If so, it does not make any changes.
    If the ID needs to be changed, it replaces the current ID files with the new ones and updates the state file.

    Args:
        id (str): The name of the new ID to use. This should be one of the IDs specified in the config file.

    Returns:
        bool: True if the ID was changed, False otherwise.

    Raises:
        FileNotFoundError: If the specified ID files are not found.
    """
    state = load_state()
    current_id = state["id"]
    id_dir = config["IDChange"].get("IDDir", os.path.join(sounds_path, "ID"))
    normal_id = config["IDChange"]["IDs"]["NormalID"]
    wx_id = config["IDChange"]["IDs"]["WXID"]
    rpt_id = config["IDChange"]["IDs"]["RptID"]

    logger.debug("changeID: ID directory: %s", id_dir)
    logger.debug("changeID: ID argument: %s", id)

    if not id:
        logger.error("changeID: called with no ID specified")
        return

    current_id = None
    if state:
        current_id = state["id"]

    logger.debug("changeID: Current ID - %s", current_id)

    if id == current_id:
        logger.debug("changeID: ID is already %s, no changes made.", id)
        return False

    if id == "NORMAL":
        logger.info("Changing to NORMAL ID")
        src_file = os.path.join(id_dir, normal_id)
        dest_file = os.path.join(id_dir, rpt_id)
        logger.debug("changeID: Copying %s to %s", src_file, dest_file)
        shutil.copyfile(src_file, dest_file)

    else:
        logger.info("Changing to %s ID", id)
        src_file = os.path.join(id_dir, wx_id)
        dest_file = os.path.join(id_dir, rpt_id)
        logger.debug("changeID: Copying %s to %s", src_file, dest_file)
        shutil.copyfile(src_file, dest_file)

    state["id"] = id
    save_state(state)

    return True


def alertScript(alerts):
    """
    This function reads a list of alerts, then performs actions based
    on the alert triggers defined in the global configuration file.

    :param alerts: List of alerts to process
    :type alerts: list[str]
    """

    # Load the saved state
    state = load_state()
    processed_alerts = state["alertscript_alerts"]
    active_alerts = state.get("active_alerts", [])  # Load active alerts from state

    # Extract only the alert names from the OrderedDict keys
    alert_names = [alert[0] for alert in alerts.keys()]

    # New alerts are those that are in the current alerts but were not active before
    new_alerts = list(set(alert_names) - set(active_alerts))

    # Update the active alerts in the state
    state["active_alerts"] = alert_names

    # Fetch AlertScript configuration from global_config
    alertScript_config = config.get("AlertScript", {})
    logger.debug("AlertScript configuration: %s", alertScript_config)

    # Fetch Mappings from AlertScript configuration
    mappings = alertScript_config.get("Mappings", [])
    if mappings is None:
        mappings = []
    logger.debug("Mappings: %s", mappings)

    # A set to hold alerts that are processed in this run
    currently_processed_alerts = set()

    # Iterate over each mapping
    for mapping in mappings:
        logger.debug("Processing mapping: %s", mapping)

        triggers = mapping.get("Triggers", [])
        commands = mapping.get("Commands", [])
        nodes = mapping.get("Nodes", [])
        match_type = mapping.get("Match", "ANY").upper()

        matched_alerts = []
        for alert in new_alerts:  # We only check the new alerts
            for trigger in triggers:
                if fnmatch.fnmatch(alert, trigger):
                    logger.debug(
                        'Match found: Alert "%s" matches trigger "%s"', alert, trigger
                    )
                    matched_alerts.append(alert)

        # Check if alerts matched the triggers as per the match type
        if (
            match_type == "ANY"
            and matched_alerts
            or match_type == "ALL"
            and len(matched_alerts) == len(triggers)
        ):
            logger.debug(
                'Alerts matched the triggers as per the match type "%s"', match_type
            )

            # Execute commands based on the Type of mapping
            for alert in matched_alerts:
                currently_processed_alerts.add(alert)

                if mapping.get("Type") == "BASH":
                    logger.debug('Mapping type is "BASH"')
                    for cmd in commands:
                        logger.info("AlertScript: Executing BASH command: %s", cmd)
                        subprocess.run(cmd, shell=True)
                elif mapping.get("Type") == "DTMF":
                    logger.debug('Mapping type is "DTMF"')
                    for node in nodes:
                        for cmd in commands:
                            dtmf_cmd = 'asterisk -rx "rpt fun {} {}"'.format(node, cmd)
                            logger.info(
                                "AlertScript: Executing DTMF command: %s", dtmf_cmd
                            )
                            subprocess.run(dtmf_cmd, shell=True)

    # Update the state with the alerts processed in this run
    state["alertscript_alerts"] = list(currently_processed_alerts)
    save_state(state)


def sendPushover(message, title=None, priority=0):
    """
    Send a push notification via the Pushover service.

    This function constructs the payload for the request, including the user key, API token, message, title, and priority.
    The payload is then sent to the Pushover API endpoint. If the request fails, an error message is logged.

    Args:
        message (str): The content of the push notification.
        title (str, optional): The title of the push notification. Defaults to None.
        priority (int, optional): The priority of the push notification. Defaults to 0.

    Raises:
        requests.exceptions.HTTPError: If an error occurs while sending the notification.
    """
    pushover_config = config["Pushover"]
    user_key = pushover_config.get("UserKey")
    token = pushover_config.get("APIToken")

    # Remove newline from the end of the message
    message = message.rstrip("\n")

    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": token,
        "user": user_key,
        "message": message,
        "title": title,
        "priority": priority,
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        logger.error("Failed to send Pushover notification: %s", response.text)


def convertAudio(audio):
    """
    Convert audio file to 8000Hz mono for compatibility with Asterisk.

    Args:
        audio (AudioSegment): Audio file to be converted.

    Returns:
        AudioSegment: Converted audio file.
    """
    return audio.set_frame_rate(8000).set_channels(1)


def change_and_log_CT_or_ID(
    alerts,
    specified_alerts,
    auto_change_enabled,
    alert_type,
    pushover_debug,
    pushover_message,
):
    """
    Check whether the CT or ID needs to be changed, performs the change, and logs the process.

    Args:
        alerts (list): The new alerts that have been fetched.
        specified_alerts (list): The alerts that require a change in CT or ID.
        auto_change_enabled (bool): Whether auto change is enabled for CT or ID.
        alert_type (str): "CT" for Courtesy Tones and "ID" for Identifiers.
        pushover_debug (bool): Whether to include debug information in pushover notifications.
        pushover_message (str): The current pushover message to which any updates will be added.
    """
    if auto_change_enabled:
        logger.debug(
            "%s auto change is enabled, alerts that require a %s change: %s",
            alert_type,
            alert_type,
            specified_alerts,
        )

        # Extract only the alert names from the OrderedDict keys
        alert_names = [alert[0] for alert in alerts.keys()]

        # Check if any alert matches specified_alerts
        # Here we replace set intersection with a list comprehension
        intersecting_alerts = [
            alert for alert in alert_names if alert in specified_alerts
        ]

        if intersecting_alerts:
            for alert in intersecting_alerts:
                logger.debug("Alert %s requires a %s change", alert, alert_type)
                if (
                    changeCT("WX") if alert_type == "CT" else changeID("WX")
                ):  # If the CT/ID was actually changed
                    if pushover_debug:
                        pushover_message += "Changed {} to WX\n".format(alert_type)
                break
        else:  # No alerts require a CT/ID change, revert back to normal
            logger.debug(
                "No alerts require a %s change, reverting to normal.", alert_type
            )
            if (
                changeCT("NORMAL") if alert_type == "CT" else changeID("NORMAL")
            ):  # If the CT/ID was actually changed
                if pushover_debug:
                    pushover_message += "Changed {} to NORMAL\n".format(alert_type)
    else:
        logger.debug("%s auto change is not enabled", alert_type)


def supermon_back_compat(alerts):
    """
    Write alerts to a file for backward compatibility with supermon.

    Args:
        alerts (OrderedDict): The alerts to write.
    """

    # Ensure the target directory exists
    os.makedirs("/tmp/AUTOSKY", exist_ok=True)

    # Get alert titles (without severity levels)
    alert_titles = [alert[0] for alert in alerts.keys()]

    # Write alert titles to a file, with each title on a new line
    with open("/tmp/AUTOSKY/warnings.txt", "w") as file:
        file.write("<br>".join(alert_titles))


def main():
    """
    The main function that orchestrates the entire process of fetching and
    processing severe weather alerts, then integrating these alerts into
    an Asterisk/app_rpt based radio repeater system.
    """
    # Fetch configurations
    say_alert_enabled = config["Alerting"].get("SayAlert", False)
    say_all_clear_enabled = config["Alerting"].get("SayAllClear", False)
    alertscript_enabled = config["AlertScript"].get("Enable", False)

    # Fetch state
    state = load_state()

    # Load old alerts
    last_alerts = state["last_alerts"]

    # Fetch new alerts
    alerts = getAlerts(countyCodes)

    # If new alerts differ from old ones, process new alerts

    if last_alerts.keys() != alerts.keys():
        new_alerts = [x for x in alerts.keys() if x not in last_alerts.keys()]
        state["last_alerts"] = alerts
        save_state(state)

        ct_alerts = config["CourtesyTones"].get("CTAlerts", [])
        enable_ct_auto_change = config["CourtesyTones"].get("Enable", False)

        id_alerts = config["IDChange"].get("IDAlerts", [])
        enable_id_auto_change = config["IDChange"].get("Enable", False)

        pushover_enabled = config["Pushover"].get("Enable", False)
        pushover_debug = config["Pushover"].get("Debug", False)

        supermon_compat_enabled = config["DEV"].get("SupermonCompat", True)
        if supermon_compat_enabled:
            supermon_back_compat(alerts)

        # Initialize pushover message
        pushover_message = (
            "Alerts Cleared\n"
            if len(alerts) == 0
            else "\n".join(str(key) for key in alerts.keys()) + "\n"
        )

        # Check if Courtesy Tones (CT) or ID needs to be changed
        change_and_log_CT_or_ID(
            alerts,
            ct_alerts,
            enable_ct_auto_change,
            "CT",
            pushover_debug,
            pushover_message,
        )
        change_and_log_CT_or_ID(
            alerts,
            id_alerts,
            enable_id_auto_change,
            "ID",
            pushover_debug,
            pushover_message,
        )

        # Check if alerts need to be communicated
        if len(alerts) == 0:
            logger.info("Alerts cleared")
            if say_all_clear_enabled:
                sayAllClear()
        else:
            logger.info("New alerts: %s", new_alerts)
            if say_alert_enabled:
                sayAlert(alerts)
            if alertscript_enabled:
                alertScript(alerts)

        # Check if tailmessage needs to be built
        enable_tailmessage = config.get("Tailmessage", {}).get("Enable", False)
        if enable_tailmessage:
            buildTailmessage(alerts)
            if pushover_debug:
                pushover_message += (
                    "WX tailmessage removed\n"
                    if not alerts
                    else "Built WX tailmessage\n"
                )

        # Send pushover notification
        if pushover_enabled:
            pushover_message = pushover_message.rstrip("\n")
            logger.debug("Sending pushover notification: %s", pushover_message)
            sendPushover(pushover_message, title="Alerts Changed")
    else:
        logger.debug("No change in alerts")


if __name__ == "__main__":
    main()
