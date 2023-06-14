# SkywarnPlus

SkywarnPlus is an optimized, powerful weather alert system designed for Asterisk/app_rpt repeater controller systems such as [AllStarLink](https://allstarlink.org/) and [HAMVOIP](https://hamvoip.org/). It's written in Python and utilizes the new [NWS CAP v1.2 JSON API](https://www.weather.gov/documentation/services-web-api). SkywarnPlus is optimized to be resource-efficient and offers customization options to suit various user needs.

Tested on ASL 1.01, ASL 2.0.0, and HAMVOIP 1.7-01.

## Features

* **Human Speech**: Provides a library of recorded human speech for clearer, more understandable alerts.
* **Performance**: Designed for minimal impact on internet bandwidth and storage, reducing unnecessary I/O operations.
* **Alert Coverage**: Allows specifying multiple counties for alerts, ensuring broad coverage.
* **Alert Filtering**: Provides advanced options to block or filter alerts using regular expressions and wildcards.
* **Remote Control**: Includes a control script that can be mapped to DTMF commands, allowing instant over-the-air control of your system.
* **Automatic Courtesy Tones**: Changes repeater courtesy tones based on active alerts.
* **Duplicate Filtering**: Ensures the same alert is never broadcast twice.
* **Selective Broadcasting**: Broadcasts alerts on weather conditions' onset or dissipation.
* **Tailmessage Management**: Provides unobtrusive alerting if alert broadcasting is disabled.
* **Pushover Integration**: Sends alerts and debug messages directly to your phone.
* **Multiple Nodes**: Supports alert distribution to as many local node numbers as desired.
* **Developer Options**: Provides a testing environment to inject manually defined alerts for testing how the system functions.

## How It Works

SkywarnPlus is a Python-based weather alert system for Asterisk/app_rpt repeater controller systems, leveraging the National Weather Service's (NWS) CAP v1.2 JSON API. The system follows several key steps to deliver timely and accurate weather alerts:

1. **Data Fetching**: The system performs regular API calls to the NWS CAP v1.2 API, which provides comprehensive, real-time data on the latest weather conditions and alerts. The frequency of these calls can be adjusted according to user needs.

2. **Data Parsing**: Upon receiving the API response, SkywarnPlus parses the JSON data to extract the information pertinent to weather alerts. This involves reading the structured JSON data and converting it into an internal format for further processing.

3. **Data Filtering**: The extracted data is then filtered based on user-defined criteria set in the configuration file. This includes narrowing down the information to specific counties of interest, as well as excluding certain types of alerts. The filtering mechanism supports regular expressions and wildcards for more sophisticated filtering rules.

4. **Alert Management**: SkywarnPlus manages the filtered alerts intelligently, ensuring that each alert is unique and relevant. Duplicate alerts are automatically removed from the pool of active alerts to prevent repetition and alert fatigue.

5. **Alert Broadcasting**: The system then broadcasts the alerts according to user-defined settings. You can customize these settings to broadcast alerts when new weather conditions are detected or when existing conditions dissipate. This ensures timely communication of weather changes.

6. **Tailmessage and Courtesy Tones**: In addition to broadcasting alerts, SkywarnPlus also automatically updates tailmessages and changes the repeater courtesy tones when specific alerts are active. These changes add a level of customization and context-awareness to the alert system and can be tailored to individual preferences.

7. **Pushover Integration**: SkywarnPlus integrates with Pushover, a mobile notification service, to send alerts and debug messages directly to your phone. This provides a direct and immediate communication channel, keeping you constantly updated on the latest weather conditions.

8. **Real Human Speech**: To enhance clarity and improve user experience, SkywarnPlus uses a library of real female human speech recordings for alerts. This creates a more natural listening experience compared to synthetic speech and aids in clear communication of alert messages.

9. **Maintenance and Resource Management**: Designed with efficiency in mind, SkywarnPlus minimizes its impact on internet bandwidth and physical storage. The system conducts its operations mindful of resource usage, making it particularly suitable for devices with limited resources, such as Raspberry Pi.

This combination of steps ensures SkywarnPlus provides reliable, timely, and accurate weather alerts, while respecting your system's resources and providing extensive customization options.

# Installation

SkywarnPlus is recommended to be installed at the `/usr/local/bin/SkywarnPlus` location on Debian (AllStarLink) and Arch (HAMVOIP) machines.

Follow the steps below to install:

1. **Dependencies**

    Install the required dependencies using the following commands:

    **Debian (AllStarLink)**
    ```bash
    apt update
    apt upgrade
    apt install git python3 python3-pip ffmpeg
    pip3 install requests python-dateutil pydub
    ```

    **Arch (HAMVOIP)**
    ```bash
    pacman -S ffmpeg
    wget https://bootstrap.pypa.io/pip/3.5/get-pip.py
    python get-pip.py
    pip install requests python-dateutil pydub
    ```

2. **Clone the Repository**

    Clone the SkywarnPlus repository from GitHub to the `/usr/local/bin` directory:

    ```bash
    cd /usr/local/bin
    git clone https://github.com/mason10198/SkywarnPlus.git
    ```
    
3. **Configure CONTROL.sh Permissions**

    The CONTROL.sh script must be made executable. Use the chmod command to change the file permissions:

    ```bash
    sudo chmod +x /usr/local/bin/SkywarnPlus/CONTROL.sh
    ```

4. **Edit Configuration**

    Edit the configuration file to suit your system:

    ```bash
    sudo nano SkywarnPlus/config.ini
    ```

5. **Crontab Entry**

    Add a crontab entry to call SkywarnPlus on an interval. Open your crontab file using the `crontab -e` command, and add the following line:

    ```bash
    * * * * * /usr/bin/python3 /usr/local/bin/SkywarnPlus/SkywarnPlus.py
    ```

    This command will execute SkywarnPlus (poll NWS API for data) every minute.

# Configuration

Edit the [config.ini](config.ini) file according to your needs. This is where you will enter your NWS codes, enable/disable specific functions, etc.

You can find your area code(s) at https://alerts.weather.gov/. Select `County List` to the right of your state, and use the `County Code` associated with the area(s) you want SkywarnPlus to poll for WX alerts.

## **IMPORTANT**: YOU WILL MISS ALERTS IF YOU USE A **ZONE** CODE. DO NOT USE **ZONE** CODES UNLESS YOU KNOW WHAT YOU ARE DOING.

According to the official [NWS API documentation](https://www.weather.gov/documentation/services-web-api):

> "For large scale or longer lasting events, such as snow storms, fire threat, or heat events, alerts are issued
by NWS public forecast zones or fire weather zones. These zones differ in size and can cross county
boundaries."

> "...county based alerts are not mapped to zones but zone based alerts are mapped to counties."

This means that if you use a County code, you will receive all alerts for both your County **AND** your Zone - but if you use a Zone code, you will **ONLY** receive alerts that cover the entire Zone, and none of the alerts specific to your County.

# Customizing the Audio Files

SkywarnPlus comes with a library of audio files that can be replaced with any 8kHz mono PCM16 WAV files you want. These are found in the `SOUNDS/` directory by default, along with `DICTIONARY.txt` which explains audio file assignments.

# Tailmessage and Courtesy Tones

SkywarnPlus offers functionalities such as Tailmessage management and Automatic Courtesy Tones, which require specific configurations in the `rpt.conf` file.

## Tailmessage

Tailmessage functionality requires the `rpt.conf` to be properly set up. Here's an example:

```ini
tailmessagetime = 600000
tailsquashedtime = 30000
tailmessagelist = /usr/local/bin/SkywarnPlus/SOUNDS/wx-tail
```

## Automatic Courtesy Tones

SkywarnPlus can automatically change the repeater courtesy tone whenever certain weather alerts are active. The configuration for this is based on your `rpt.conf` file setup. Here's an example:

```ini
[NODENUMBER]
unlinkedct = ct1
remotect = ct1
linkunkeyct = ct2
[telemetry]
ct1 = /usr/local/bin/SkywarnPlus/SOUNDS/TONES/CT-LOCAL
ct2 = /usr/local/bin/SkywarnPlus/SOUNDS/TONES/CT-LINK
remotetx = /usr/local/bin/SkywarnPlus/SOUNDS/TONES/CT-LOCAL
```
Courtesy tone files are located in `SOUNDS/TONES` by default and are configured through `config.ini` and `rpt.conf`.

# Pushover Integration

SkywarnPlus can use the free Pushover API to send WX alert notifications and debug messages directly to your smartphone or other devices.
1. Visit https://pushover.net/ to sign up for a free account.
2. Find your UserKey on your main dashboard
3. Scroll down and create an Application/API key for your node
4. Add UserKey & API Key to `config.ini`

# Control Script

SkywarnPlus comes with a powerful control script (`CONTROL.sh`) that can be used to enable or disable certain SkywarnPlus functions. This script is particularly useful when you want to map DTMF control codes to these functions. An added advantage is that the script provides spoken feedback upon execution, making it even more suitable for DTMF control.

## Usage 

To use the CONTROL.sh script, you need to call it with two parameters:

1. The name of the setting you want to change (case insensitive).

    - Enable (Completely enable/disable SkywarnPlus)
    - SayAlert
    - SayAllClear
    - TailMessage
    - CourtesyTone

2. The new value for the setting (either 'true' or 'false' or 'toggle').

For example, to completely disable SkywarnPlus, you would use:

```bash
/usr/local/bin/SkywarnPlus/CONTROL.sh enable false
```

And to reenable it, you would use:

```bash
/usr/local/bin/SkywarnPlus/CONTROL.sh enable true
```

And to toggle it, you would use:

```bash
/usr/local/bin/SkywarnPlus/CONTROL.sh enable toggle
```

## Spoken Feedback

Upon the successful execution of a control command, the `CONTROL.sh` script will provide spoken feedback that corresponds to the change made. For instance, if you execute a command to enable the SayAlert function, the script will play an audio message stating that SayAlert has been enabled. This feature enhances user experience and confirms that the desired changes have been effected.

## Mapping to DTMF Control Codes

You can map the CONTROL.sh script to DTMF control codes in the `rpt.conf` file of your node. Here is an example of how to do this:

```bash
801 = cmd,/usr/local/bin/SkywarnPlus/CONTROL.sh enable toggle ; Toggles SkywarnPlus
802 = cmd,/usr/local/bin/SkywarnPlus/CONTROL.sh sayalert toggle ; Toggles SayAlert
803 = cmd,/usr/local/bin/SkywarnPlus/CONTROL.sh sayallclear toggle ; Toggles SayAllClear
804 = cmd,/usr/local/bin/SkywarnPlus/CONTROL.sh tailmessage toggle ; Toggles TailMessage
805 = cmd,/usr/local/bin/SkywarnPlus/CONTROL.sh courtesytone toggle ; Toggles CourtesyTone
```

With this setup, you can control SkywarnPlus' functionality using DTMF commands.

# Testing

SkywarnPlus provides the ability to inject predefined alerts, bypassing the call to the NWS API. This feature is extremely useful for testing SkywarnPlus.

To enable this option, modify the following settings in the `[DEV]` section of your `config.ini` file:

```ini
; Enable to inject the below list of test alerts instead of calling the NWS API
INJECT = True

; CASE SENSITIVE, comma & newline separated list of alerts to inject
INJECTALERTS = Tornado Warning,
               Tornado Watch,
               Severe Thunderstorm Warning
```

# Debugging

Debugging is an essential part of diagnosing issues with SkywarnPlus. To facilitate this, SkywarnPlus provides a built-in debugging feature. Here's how to use it:

1. **Enable Debugging**: The debugging feature can be enabled in the `config.ini` file. Open this file and set the `debug` option under the `[SkywarnPlus]` section to `true`.

```ini
; Logging Options
[Logging]
; Enable more verbose logging
; Either True or False
Debug = False
```

This will allow the program to output detailed information about its operations, which is helpful for identifying any issues or errors.

2. **Open an Asterisk Console**: While debugging SkywarnPlus, it's helpful to have an Asterisk console open in a separate terminal window. This allows you to observe any issues related to Asterisk, such as problems playing audio files.

You can open an Asterisk console with the following command:

```bash
asterisk -rvvv
```

This command will launch an Asterisk console with a verbose output level of 3 (`vvv`), which provides a detailed look at what Asterisk is doing. This can be particularly useful if you're trying to debug issues with audio playback.

3. **Analyze Debugging Output**: With debugging enabled in SkywarnPlus and the Asterisk console open, you can now run SkywarnPlus and observe the detailed output in both terminals. This information can be used to identify and troubleshoot any issues or unexpected behaviors.

Remember, the more detailed your debug output is, the easier it will be to spot any issues. However, please be aware that enabling debug mode can result in large amounts of output, so it should be used judiciously.

If you encounter any issues that you're unable to resolve, please don't hesitate to submit a detailed bug report on the [SkywarnPlus GitHub Repository](https://github.com/mason10198/SkywarnPlus).

# Maintenance and Bug Reporting

SkywarnPlus is actively maintained by a single individual who dedicates their spare time to improve and manage this project. Despite best efforts, the application may have some bugs or areas for improvement.

If you encounter any issues with SkywarnPlus, please check back to the [SkywarnPlus GitHub Repository](https://github.com/mason10198/SkywarnPlus) to see if there have been any updates or fixes since the last time you downloaded it. New commits are made regularly to enhance the system's performance and rectify any known issues.

Bug reporting is greatly appreciated as it helps to improve SkywarnPlus. If you spot a bug, please raise an issue in the GitHub repository detailing the problem. Include as much information as possible, such as error messages, screenshots, and steps to reproduce the issue. This will assist in quickly understanding and resolving the issue. 

Thank you for your understanding and assistance in making SkywarnPlus a more robust and reliable system for all.

# Contributing

SkywarnPlus is open-source and welcomes contributions. If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are warmly welcome.

# License

SkywarnPlus is open-sourced software licensed under the [MIT license](LICENSE).

Created by Mason Nelson (N5LSN/WRKF394)