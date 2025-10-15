#!/usr/bin/python3
"""
CustomAlertScript.py

This is an example script that can be ran by cron at custom intervals.
This script is a simplifies version of the AlertScript function included in SkywarnPlus.
It will check the last alerts from SkywarnPlus and execute commands associated with them.

The purpose of this is to allow you to run AlertScript commands at custom intervals,
rather than only running commands when alerts are first detected.

Example:
Trigger SkyDescribe.py for all alerts that contain the word "Warning" in the title, once per hour.
Crontab entry: 0 * * * * /usr/local/bin/SkywarnPlus/CustomAlertScript.py

You can create as many copies of this script as you want to execute different commands at different intervals.
"""

import json
import subprocess
import fnmatch
from functools import lru_cache

# The trigger alerts and associated commands
# Replace or add more trigger commands as required.

# Path to the SkywarnPlus data file
DATA_FILE = '/tmp/SkywarnPlus/data.json'

# Alert triggers & commands
TRIGGER_ALERTS = {
    # Trigger SkyDescribe.py for all alerts that contain the word "Warning" in the title
    "*Warning": "/usr/local/bin/SkywarnPlus/SkyDescribe.py \"{alert_title}\"",
}

def match_trigger(alert_title):
    for pattern, command in TRIGGER_ALERTS.items():
        if fnmatch.fnmatch(alert_title, pattern):
            return command.format(alert_title=alert_title)
    return None

@lru_cache(maxsize=1)
def _load_data():
    """Load data with caching."""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def main():
    # Load the data with caching
    data = _load_data()

    # Check if the trigger alerts are in the last alerts
    for alert in data["last_alerts"]:
        command = match_trigger(alert[0])
        if command:
            print("Executing command for alert: {}".format(alert[0]))
            try:
                subprocess.run(command, shell=True, timeout=30, check=False)
            except subprocess.TimeoutExpired:
                print(f"Subprocess timeout for command: {command}")
            except Exception as e:
                print(f"Subprocess error for command {command}: {e}")

if __name__ == "__main__":
    main()