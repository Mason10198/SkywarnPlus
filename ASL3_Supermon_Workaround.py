#!/usr/bin/python3

"""
ASL3_Supermon_Workaround.py by Mason Nelson
===============================================================================
This script is a workaround for the Supermon compatibility issue with ASL 3.
With Asterisk 20 no longer running as the root user, SkywarnPlus is unable to
write to the old AUTOSKY directories. This script can be added to the crontab
with root privileges as a workaround to write the alerts to the old AUTOSKY
directories for Supermon compatibility.

This file is part of SkywarnPlus.
SkywarnPlus is free software: you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version. SkywarnPlus is distributed in the hope
that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with SkywarnPlus. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import json
import logging
from collections import OrderedDict

# Paths
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
COUNTY_CODES_PATH = os.path.join(BASE_DIR, "CountyCodes.md")
DATA_FILE = "/tmp/SkywarnPlus/data.json"

# Logging setup
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

def load_state():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            state = json.load(file)
            state["last_alerts"] = OrderedDict((x[0], x[1]) for x in state.get("last_alerts", []))
            return state
    logging.error("Data file not found, returning initial state")
    return {"last_alerts": OrderedDict()}

def generate_title_string(alerts, county_data):
    alert_titles_with_counties = []
    for alert in alerts:
        counties = sorted(set(replace_with_county_name(x["county_code"], county_data) for x in alerts[alert]))
        alert_titles_with_counties.append("{} [{}]".format(alert, ", ".join(counties)))
    logging.info("String generated: %s", alert_titles_with_counties)
    return alert_titles_with_counties

def supermon_back_compat(alerts, county_data):
    if os.getuid() != 0:
        logging.error("Not running as root, exiting function")
        return
    alert_titles_with_counties = generate_title_string(alerts, county_data)
    for path in ["/tmp/AUTOSKY", "/var/www/html/AUTOSKY"]:
        try:
            os.makedirs(path, exist_ok=True)
            if os.access(path, os.W_OK):
                file_path = os.path.join(path, "warnings.txt")
                with open(file_path, "w") as file:
                    file.write("<br>".join(alert_titles_with_counties))
            else:
                logging.error("No write permission for %s", path)
        except Exception as e:
            logging.error("An error occurred while writing to %s: %s", path, e)

def load_county_names(md_file):
    with open(md_file, "r") as f:
        lines = f.readlines()
    county_data = {}
    in_table = False
    for line in lines:
        if line.startswith("| County |"):
            in_table = True
            continue
        elif not in_table or line.strip() == "" or line.startswith("##"):
            continue
        else:
            name, code = [s.strip() for s in line.split("|")[1:-1]]
            county_data[code] = name
    return county_data

def replace_with_county_name(county_code, county_data):
    county_name = county_data.get(county_code, county_code)
    return county_name

def main():
    if not os.path.isfile(DATA_FILE):
        logging.warning("Data file does not exist, exiting.")
        exit()
    state = load_state()
    last_alerts = state["last_alerts"]
    county_data = load_county_names(COUNTY_CODES_PATH)
    supermon_back_compat(last_alerts, county_data)
if __name__ == "__main__":
    main()