#!/usr/bin/python3

"""
SkywarnPlus v0.2.0 by Mason Nelson (N5LSN/WRKF394)
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
import yaml
from datetime import datetime, timezone
from dateutil import parser
from pydub import AudioSegment

# Directories and Paths
baseDir = os.path.dirname(os.path.realpath(__file__))
configPath = os.path.join(baseDir, "config.yaml")

# Open and read configuration file
with open(configPath, "r") as config_file:
    config = yaml.safe_load(config_file)

# Check if SkywarnPlus is enabled
master_enable = config.get("SKYWARNPLUS", {}).get("Enable", False)
if not master_enable:
    print("SkywarnPlus is disabled in config.yaml, exiting...")
    exit()

# Define tmp_dir and sounds_path
tmp_dir = config.get("DEV", {}).get("TmpDir", "/tmp/SkywarnPlus")
sounds_path = config.get("Alerting", {}).get("SoundsPath", os.path.join(baseDir, "SOUNDS"))

# Define countyCodes
countyCodes = config.get("Alerting", {}).get("CountyCodes", [])

# Create tmp_dir if it doesn't exist
if tmp_dir:
    os.makedirs(tmp_dir, exist_ok=True)
else:
    print("Error: tmp_dir is not set.")

# Define Blocked events
global_blocked_events = (
    config.get("Blocking", {}).get("GlobalBlockedEvents", [])
)
if global_blocked_events is None:
    global_blocked_events = []
sayalert_blocked_events = (
    config.get("Blocking", {}).get("SayAlertBlockedEvents", [])
)
if sayalert_blocked_events is None:
    sayalert_blocked_events = []
tailmessage_blocked_events = (
    config.get("Blocking", {}).get("TailmessageBlockedEvents", [])
)
if tailmessage_blocked_events is None:
    tailmessage_blocked_events = []

# Define Max Alerts
max_alerts = config.get("Alerting", {}).get("MaxAlerts", 99)

# Define Tailmessage configuration
tailmessage_config = config.get("Tailmessage", {})
enable_tailmessage = tailmessage_config.get("Enable", False)
tailmessage_file = tailmessage_config.get(
    "TailmessagePath", os.path.join(sounds_path, "wx-tail.wav")
)

# Define IDChange configuration
idchange_config = config.get("IDChange", {})
enable_idchange = idchange_config.get("Enable", False)

# Data file path
data_file = os.path.join(tmp_dir, "data.json")

# Define Warning and Announcement strings
WS = [
    "Hurricane Force Wind Warning",
    "Severe Thunderstorm Warning",
    "Severe Thunderstorm Watch",
    "Winter Weather Advisory",
    "Tropical Storm Warning",
    "Special Marine Warning",
    "Freezing Rain Advisory",
    "Special Weather Statement",
    "Excessive Heat Warning",
    "Coastal Flood Advisory",
    "Coastal Flood Warning",
    "Winter Storm Warning",
    "Tropical Storm Watch",
    "Thunderstorm Warning",
    "Small Craft Advisory",
    "Extreme Wind Warning",
    "Excessive Heat Watch",
    "Wind Chill Advisory",
    "Storm Surge Warning",
    "River Flood Warning",
    "Flash Flood Warning",
    "Coastal Flood Watch",
    "Winter Storm Watch",
    "Wind Chill Warning",
    "Thunderstorm Watch",
    "Fire Weather Watch",
    "Dense Fog Advisory",
    "Storm Surge Watch",
    "River Flood Watch",
    "Ice Storm Warning",
    "Hurricane Warning",
    "High Wind Warning",
    "Flash Flood Watch",
    "Red Flag Warning",
    "Blizzard Warning",
    "Tornado Warning",
    "Hurricane Watch",
    "High Wind Watch",
    "Frost Advisory",
    "Freeze Warning",
    "Wind Advisory",
    "Tornado Watch",
    "Storm Warning",
    "Heat Advisory",
    "Flood Warning",
    "Gale Warning",
    "Freeze Watch",
    "Flood Watch",
    "Flood Advisory",
    "Hurricane Local Statement",
    "Beach Hazards Statement",
    "Air Quality Alert",
    "Severe Weather Statement",
    "Winter Storm Advisory",
    "Tropical Storm Advisory",
    "Blizzard Watch",
    "Dust Storm Warning",
    "High Surf Advisory",
    "Heat Watch",
    "Freeze Watch",
    "Dense Smoke Advisory",
    "Avalanche Warning",
]
WA = [
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "43",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
    "51",
    "52",
    "53",
    "54",
    "55",
    "56",
    "57",
    "58",
    "59",
    "60",
    "61",
    "62",
]

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
        dict: A dictionary containing courtesy tone (ct), identifier (id) and alerts.
    """
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            state = json.load(file)
            # state["alertscript_alerts"] = set(state["alertscript_alerts"])
            # state["last_alerts"] = set(state["last_alerts"])
            return state
    else:
        return {
            "ct": None,
            "id": None,
            "alertscript_alerts": set(),
            "last_alerts": set(),
        }


def save_state(state):
    """
    Save the state to the state file.

    Args:
        state (dict): A dictionary containing courtesy tone (ct), identifier (id) and alerts.
    """
    state["alertscript_alerts"] = list(state["alertscript_alerts"])
    state["last_alerts"] = list(state["last_alerts"])
    with open(data_file, "w") as file:
        json.dump(state, file)


def getAlerts(countyCodes):
    """
    Retrieve severe weather alerts for specified county codes.

    Args:
        countyCodes (list): List of county codes.

    Returns:
        alerts (list): List of active weather alerts.
                       In case of alert injection from the config, return the injected alerts.
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

    # Inject alerts if DEV INJECT is enabled in the config
    if config.get("DEV", {}).get("INJECT", False):
        logger.debug("getAlerts: DEV Alert Injection Enabled")
        alerts = [
            alert.strip() for alert in config["DEV"].get("INJECTALERTS", [])
        ]
        logger.debug("getAlerts: Injecting alerts: %s", alerts)
        return alerts

    alerts = []
    current_time = datetime.now(timezone.utc)

    for countyCode in countyCodes:
        url = "https://api.weather.gov/alerts/active?zone={}".format(countyCode)
        logger.debug("getAlerts: Checking for alerts in %s at URL: %s", countyCode, url)
        response = requests.get(url)

        if response.status_code == 200:
            alert_data = response.json()
            for feature in alert_data["features"]:
                effective = feature["properties"].get("effective")
                expires = feature["properties"].get("expires")
                if effective and expires:
                    effective_time = parser.isoparse(effective)
                    expires_time = parser.isoparse(expires)
                    if effective_time <= current_time < expires_time:
                        event = feature["properties"]["event"]
                        for global_blocked_event in global_blocked_events:
                            if fnmatch.fnmatch(event, global_blocked_event):
                                logger.debug(
                                    "getAlerts: Globally Blocking %s as per configuration",
                                    event,
                                )
                                break
                        else:
                            severity = feature["properties"].get("severity", None)
                            if severity is None:
                                last_word = event.split()[-1]
                                severity = severity_mapping_words.get(last_word, 0)
                            else:
                                severity = severity_mapping_api.get(severity, 0)
                            alerts.append(
                                (event, severity)
                            )  # Add event to list as a tuple
        else:
            logger.error(
                "Failed to retrieve alerts for %s, HTTP status code %s, response: %s",
                countyCode,
                response.status_code,
                response.text,
            )

    alerts = list(dict.fromkeys(alerts))

    alerts.sort(
        key=lambda x: (
            x[1],  # API-provided severity
            severity_mapping_words.get(x[0].split()[-1], 0),  # 'words' severity
        ),
        reverse=True,
    )

    logger.debug("getAlerts: Sorted alerts - (alert), (severity)")
    for alert in alerts:
        logger.debug(alert)

    alerts = [alert[0] for alert in alerts[:max_alerts]]

    return alerts


def sayAlert(alerts):
    """
    Generate and broadcast severe weather alert sounds on Asterisk.

    Args:
        alerts (list): List of active weather alerts.
    """
    # Define the path of the alert file
    alert_file = "{}/alert.wav".format(sounds_path)

    combined_sound = AudioSegment.from_wav(
        os.path.join(sounds_path, "ALERTS", "SWP97.wav")
    )
    sound_effect = AudioSegment.from_wav(
        os.path.join(sounds_path, "ALERTS", "SWP95.wav")
    )

    alert_count = 0

    for alert in alerts:
        if any(
            fnmatch.fnmatch(alert, blocked_event)
            for blocked_event in sayalert_blocked_events
        ):
            logger.debug("sayAlert: blocking %s as per configuration", alert)
            continue

        try:
            index = WS.index(alert)
            audio_file = AudioSegment.from_wav(
                os.path.join(sounds_path, "ALERTS", "SWP{}.wav".format(WA[index]))
            )
            combined_sound += sound_effect + audio_file
            logger.debug(
                "sayAlert: Added %s (SWP%s.wav) to alert sound", alert, WA[index]
            )
            alert_count += 1
        except ValueError:
            logger.error("sayAlert: Alert not found: %s", alert)
        except FileNotFoundError:
            logger.error(
                "sayAlert: Audio file not found: %s/ALERTS/SWP%s.wav",
                sounds_path,
                WA[index],
            )

    if alert_count == 0:
        logger.debug("sayAlert: All alerts were blocked, not broadcasting any alerts.")
    else:
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

        logger.info("Waiting 30 seconds for Asterisk to make announcement...")
        time.sleep(30)


def sayAllClear():
    """
    Generate and broadcast 'all clear' message on Asterisk.
    """
    alert_clear = os.path.join(sounds_path, "ALERTS", "SWP96.wav")

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
    if not alerts:
        logger.debug("buildTailMessage: No alerts, creating silent tailmessage")
        silence = AudioSegment.silent(duration=100)
        converted_silence = convertAudio(silence)
        converted_silence.export(tailmessage_file, format="wav")
        return

    combined_sound = AudioSegment.empty()
    sound_effect = AudioSegment.from_wav(
        os.path.join(sounds_path, "ALERTS", "SWP95.wav")
    )

    for alert in alerts:
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
                os.path.join(sounds_path, "ALERTS", "SWP{}.wav".format(WA[index]))
            )
            combined_sound += sound_effect + audio_file
            logger.debug(
                "buildTailMessage: Added %s (SWP%s.wav) to tailmessage",
                alert,
                WA[index],
            )
        except ValueError:
            logger.error("Alert not found: %s", alert)
        except FileNotFoundError:
            logger.error(
                "Audio file not found: %s/ALERTS/SWP%s.wav",
                sounds_path,
                WA[index],
            )

    if combined_sound.empty():
        logger.debug(
            "buildTailMessage: All alerts were blocked, creating silent tailmessage"
        )
        combined_sound = AudioSegment.silent(duration=100)

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
    tone_dir = config["CourtesyTones"].get("ToneDir", os.path.join(sounds_path, "TONES"))
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
    # Fetch AlertScript configuration from global_config
    alertScript_config = config.get("AlertScript", {})
    logger.debug("AlertScript configuration: %s", alertScript_config)

    # Fetch Mappings from AlertScript configuration
    mappings = alertScript_config.get("Mappings", [])
    if mappings is None:
        mappings = []
    logger.debug("Mappings: %s", mappings)

    # Iterate over each mapping
    for mapping in mappings:
        logger.debug("Processing mapping: %s", mapping)

        triggers = mapping.get("Triggers", [])
        commands = mapping.get("Commands", [])
        nodes = mapping.get("Nodes", [])
        match_type = mapping.get("Match", "ANY").upper()

        matched_alerts = []
        for alert in alerts:
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
            if mapping.get("Type") == "BASH":
                logger.debug('Mapping type is "BASH"')
                for cmd in commands:
                    logger.debug("Executing BASH command: %s", cmd)
                    subprocess.run(cmd, shell=True)
            elif mapping.get("Type") == "DTMF":
                logger.debug('Mapping type is "DTMF"')
                for node in nodes:
                    for cmd in commands:
                        dtmf_cmd = 'asterisk -rx "rpt fun {} {}"'.format(node, cmd)
                        logger.debug("Executing DTMF command: %s", dtmf_cmd)
                        subprocess.run(dtmf_cmd, shell=True)


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
        # Check if any alert matches specified_alerts
        if set(alerts).intersection(specified_alerts):
            for alert in alerts:
                if alert in specified_alerts:
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


def main():
    """
    The main function that orchestrates the entire process of fetching and
    processing severe weather alerts, then integrating these alerts into
    an Asterisk/app_rpt based radio repeater system.

    Key Steps:
    1. Fetch the configuration from the local setup.
    2. Get the new alerts based on the provided county codes.
    3. Compare the new alerts with the previously stored alerts.
    4. If there's a change, store the new alerts and process them accordingly.
    5. Check each alert against a set of specified alert types and perform actions accordingly.
    6. Send notifications if enabled.
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
    if last_alerts != alerts:
        state["last_alerts"] = alerts
        save_state(state)

        ct_alerts = config["CourtesyTones"].get("CTAlerts", [])
        enable_ct_auto_change = config["CourtesyTones"].get("Enable", False)

        id_alerts = config["IDChange"].get("IDAlerts", [])
        enable_id_auto_change = config["IDChange"].get("Enable", False)

        pushover_enabled = config["Pushover"].get("Enable", False)
        pushover_debug = config["Pushover"].get("Debug", False)

        # Initialize pushover message
        pushover_message = (
            "Alerts Cleared\n" if len(alerts) == 0 else "\n".join(alerts) + "\n"
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
            logger.info("No alerts found")
            if say_all_clear_enabled:
                sayAllClear()
        else:
            logger.info("Alerts found: %s", alerts)
            if alertscript_enabled:
                alertScript(alerts)
            if say_alert_enabled:
                sayAlert(alerts)

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
