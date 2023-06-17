#!/bin/bash

# CONTROL.sh
# A Control Script for SkywarnPlus v0.1.0
# by Mason Nelson (N5LSN/WRKF394)
#
#
# This script allows you to change the value of specific keys in the SkywarnPlus config.ini file.
# It's designed to enable or disable certain features of SkywarnPlus from the command line.
# It is case-insensitive, accepting both upper and lower case parameters.
#
# Usage: ./CONTROL.sh <key> <value>
# Example: ./CONTROL.sh sayalert false
# This will set 'SayAlert' to 'False' in the config.ini file.
#
# Supported keys:
# - enable: Enable or disable SkywarnPlus entirely. (Section: SKYWARNPLUS)
# - sayalert: Enable or disable instant alerting when weather alerts change. (Section: Alerting)
# - sayallclear: Enable or disable instant alerting when weather alerts are cleared. (Section: Alerting)
# - tailmessage: Enable or disable building of tail message. (Section: Tailmessage)
# - courtesytone: Enable or disable automatic courtesy tones. (Section: CourtesyTones)
#
# Supported values:
# - true: Enable the feature.
# - false: Disable the feature.
# - toggle: Toggle the feature.
#
# All changes will be made in the config.ini file located in the same directory as the script.

# First, we need to check if the correct number of arguments are passed
if [ "$#" -ne 2 ]; then
    echo "Incorrect number of arguments. Please provide the key and the new value."
    echo "Usage: $0 <key> <value>"
    exit 1
fi

# Get the directory of the script
SCRIPT_DIR=$(dirname $(readlink -f $0))
CONFIG_FILE="${SCRIPT_DIR}/config.ini"

# Convert the input key into lowercase
KEY=$(echo "$1" | tr '[:upper:]' '[:lower:]')

# Convert the first character of the value to uppercase
VALUE=$(echo "$2" | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')

# Make sure the provided value is either 'True' or 'False' or 'Toggle'
if [[ "${VALUE^^}" != "TRUE" && "${VALUE^^}" != "FALSE" && "${VALUE^^}" != "TOGGLE" ]]; then
    echo "Invalid value. Please provide either 'true' or 'false' or 'toggle'."
    exit 1
fi

# Define the command-line arguments and their corresponding keys in the configuration file
declare -A ARGUMENTS=( ["enable"]="Enable" ["sayalert"]="SayAlert" ["sayallclear"]="SayAllClear" ["tailmessage"]="Enable" ["courtesytone"]="Enable")

# Define the sections in the configuration file that each key belongs to
declare -A SECTIONS=( ["enable"]="SKYWARNPLUS" ["sayalert"]="Alerting" ["sayallclear"]="Alerting" ["tailmessage"]="Tailmessage" ["courtesytone"]="CourtesyTones")

# Define the audio files associated with each key
declare -A AUDIO_FILES_ENABLED=( ["enable"]="SWP85.wav" ["sayalert"]="SWP87.wav" ["sayallclear"]="SWP89.wav" ["tailmessage"]="SWP91.wav" ["courtesytone"]="SWP93.wav")

declare -A AUDIO_FILES_DISABLED=( ["enable"]="SWP86.wav" ["sayalert"]="SWP88.wav" ["sayallclear"]="SWP90.wav" ["tailmessage"]="SWP92.wav" ["courtesytone"]="SWP94.wav")

# Read the node number and path to SOUNDS directory from the config.ini
NODES=$(awk -F " = " '/^Nodes/ {print $2}' "${SCRIPT_DIR}/config.ini" | tr -d ' ' | tr ',' '\n')

# Check if the input key is valid
if [[ ${ARGUMENTS[$KEY]+_} ]]; then
    # Get the corresponding key in the configuration file
    CONFIG_KEY=${ARGUMENTS[$KEY]}
    
    # Get the section that the key belongs to
    SECTION=${SECTIONS[$KEY]}
    
    if [[ "${VALUE^^}" = "TOGGLE" ]]; then
        CONFIG_VALUE=$(awk -F "=" -v section="$SECTION" -v key="$KEY" '
        BEGIN {RS=";"; FS="="}
        $0 ~ "\\[" section "\\]" {flag=1}
        flag && $1 ~ key {gsub(/ /, "", $2); print toupper($2); exit}
        $0 ~ "\\[" && $0 !~ "\\[" section "\\]" {flag=0}' "$CONFIG_FILE")
        
        # Remove leading and trailing whitespace
        CURRENT_VALUE=$(echo $CONFIG_VALUE | xargs)
        
        if [ "$CURRENT_VALUE" == "TRUE" ]; then
            NEW_VALUE="False"
            elif [ "$CURRENT_VALUE" == "FALSE" ]; then
            NEW_VALUE="True"
        else
            echo "Could not determine current value. Exiting."
            exit 1
        fi
        VALUE=$NEW_VALUE
    fi
    
    # Update the value of the key in the configuration file
    sed -i "/^\[${SECTION}\]/,/^\[/{s/^${CONFIG_KEY} = .*/${CONFIG_KEY} = ${VALUE}/}" "${SCRIPT_DIR}/config.ini"
    
    # Get the correct audio file based on the new value
    if [ "$VALUE" = "True" ]; then
        AUDIO_FILE=${AUDIO_FILES_ENABLED[$KEY]}
    else
        AUDIO_FILE=${AUDIO_FILES_DISABLED[$KEY]}
    fi
    
    # Play the corresponding audio message on all nodes
    for NODE in $NODES; do
        /usr/sbin/asterisk -rx "rpt localplay ${NODE} ${SCRIPT_DIR}/SOUNDS/ALERTS/${AUDIO_FILE%.*}"
    done
else
    echo "The provided key does not match any configurable item."
    exit 1
fi