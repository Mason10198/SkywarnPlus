# SkywarnPlus: Your Advanced Weather Alert System

SkywarnPlus is a sophisticated software solution that works hand-in-hand with your AllStarLink (Debian) or HAMVOIP (Arch) node to keep you informed and ready for whatever the weather brings. Combining weather data with intuitive features, SkywarnPlus optimizes the efficiency and functionality of your node.

## Key Features

- **Seamless Integration:** SkywarnPlus operates on a Debian (AllStarLink) or Arch (HAMVOIP) node.

- **Real-Time Weather Alerts:** The software checks the NWS CAP v1.2 API for live weather alerts for user-defined areas.

- **Unlimited Area & Node Numbers:** Users can define as many areas and local node numbers as desired.

- **Automatic Announcements:** Weather alerts, including when all warnings have been cleared, are announced automatically on the node.

- **Tailmessage Creation:** The software generates tailmessages for the node to continuously inform listeners about active alerts after the initial broadcast.

- **Dynamic Changes to Node:** Courtesy tones and node CW / voice ID automatically change according to user-defined alerts, optimizing communication during severe weather.

- **Human Speech:** Announcements are delivered in a natural, human speech for easier understanding.

- **Efficiency & Speed:** SkywarnPlus is optimized for speed and efficiency to provide real-time information without delay.

- **Preserves Hardware:** SkywarnPlus limits I/O to the physical disk, preventing SD card burnout in Raspberry Pi devices.

- **Remote Control:** Functions can be mapped to DTMF commands for remote over-the-air control.

- **Highly Customizable:** SkywarnPlus is extremely customizable, offering advanced filtering parameters to block certain alerts or types of alerts from different functions. Users can even map DTMF macros or shell commands to specified weather alerts, expanding the software's capabilities according to user needs.

- **Pushover Integration:** With Pushover integration, SkywarnPlus can send weather alert notifications directly to your phone or other devices.

Whether you wish to auto-link to a Skywarn net during severe weather, program your node to control an external device like a siren during a tornado warning, or simply want to stay updated on changing weather conditions, SkywarnPlus offers a comprehensive, efficient, and customizable solution for your weather alert needs.

# Installation

SkywarnPlus is recommended to be installed at the `/usr/local/bin/SkywarnPlus` location on Debian (AllStarLink) and Arch (HAMVOIP) machines.

Follow the steps below to install:

1. **Dependencies**

   Install the required dependencies using the following commands:

   **Debian (AllStarLink)**

   ```bash
   apt update
   apt upgrade
   apt install unzip python3 python3-pip ffmpeg
   pip3 install pyyaml requests python-dateutil pydub
   ```

   **Arch (HAMVOIP)**

   It is a good idea to first update your HAMVOIP system using **Option 1** in the HAMVOIP menu before installing the dependencies.

   ```bash
   pacman -S ffmpeg
   wget https://bootstrap.pypa.io/pip/3.5/get-pip.py
   python get-pip.py
   pip install pyyaml requests python-dateutil pydub
   ```

2. **Download SkywarnPlus**

   Download the latest release of SkywarnPlus from GitHub

   ```bash
   cd /usr/local/bin
   wget https://github.com/Mason10198/SkywarnPlus/releases/latest/download/SkywarnPlus.zip
   unzip SkywarnPlus.zip
   rm SkywarnPlus.zip
   ```

3. **Configure Permissions**

   The scripts must be made executable. Use the chmod command to change the file permissions:

   ```bash
   cd SkywarnPlus
   chmod +x SkywarnPlus.py
   chmod +x SkyControl.py
   ```

4. **Edit Configuration**

    Edit the [config.yaml](config.yaml) file according to your needs. This is where you will enter your NWS codes, enable/disable specific functions, etc.

   ```bash
   nano config.yaml
   ```

    You can find your area code(s) at https://alerts.weather.gov/. Select `County List` to the right of your state, and use the `County Code` associated with the area(s) you want SkywarnPlus to poll for WX alerts.

    ## **IMPORTANT**: YOU WILL MISS ALERTS IF YOU USE A **ZONE** CODE. DO NOT USE **ZONE** CODES UNLESS YOU KNOW WHAT YOU ARE DOING.

    According to the official [NWS API documentation](https://www.weather.gov/documentation/services-web-api):

    > "For large scale or longer lasting events, such as snow storms, fire threat, or heat events, alerts are issued
    > by NWS public forecast zones or fire weather zones. These zones differ in size and can cross county
    > boundaries."

    > "...county based alerts are not mapped to zones but zone based alerts are mapped to counties."

    This means that if you use a County code, you will receive all alerts for both your County **AND** your Zone - but if you use a Zone code, you will **ONLY** receive alerts that cover the entire Zone, and none of the alerts specific to your County.

5. **Crontab Entry**

   Add a crontab entry to call SkywarnPlus on an interval. Open your crontab file using the `crontab -e` command, and add the following line:

   ```bash
   * * * * * /usr/local/bin/SkywarnPlus/SkywarnPlus.py
   ```

   This command will execute SkywarnPlus (poll NWS API for data) every minute.

# Tailmessage, Courtesy Tones, & IDs

SkywarnPlus can automatically change and manage tailmessages, courtesy tones, and CW / voice IDs on your node. These functions require specific configurations in the `rpt.conf` file.

## Tailmessage

SkywarnPlus can automatically create, manage, and remove a tailmessage whenever certain weather alerts are active to keep listeners informed throught the duration of active alerts. The configuration for this is based on your `rpt.conf` file setup. Here's an example:

```ini
tailmessagetime = 600000
tailsquashedtime = 30000
tailmessagelist = /usr/local/bin/SkywarnPlus/SOUNDS/wx-tail
```

## Courtesy Tones

SkywarnPlus can automatically change the node courtesy tone whenever certain weather alerts are active. The configuration for this is based on your `rpt.conf` file setup. Here's an example:

```ini
[NODENUMBER]
unlinkedct = ct1
remotect = ct1
linkunkeyct = ct2
[telemetry]
ct1 = /usr/local/bin/SkywarnPlus/SOUNDS/TONES/CT1
ct2 = /usr/local/bin/SkywarnPlus/SOUNDS/TONES/CT2
remotetx = /usr/local/bin/SkywarnPlus/SOUNDS/TONES/CT1
```

## CW / Voice IDs
SkywarnPlus can automatically change the node ID whenever certain weather alerts are active. The configuration for this is based on your `rpt.conf` file setup. Here's an example:
```ini
[NODENUMBER]
idrecording = /usr/local/bin/SkywarnPlus/SOUNDS/ID/RPTID
```

# Pushover Integration

SkywarnPlus can use the free Pushover API to send WX alert notifications and debug messages directly to your smartphone or other devices.

1. Visit https://pushover.net/ to sign up for a free account.
2. Find your UserKey on your main dashboard
3. Scroll down and create an Application/API key for your node
4. Add UserKey & API Key to `config.yaml`

# Control Script

SkywarnPlus comes with a powerful control script (`SkyControl.py`) that can be used to enable or disable certain SkywarnPlus functions via shell, without manually editing `config.yaml`. This script is particularly useful when you want to map DTMF control codes to these functions. An added advantage is that the script provides spoken feedback upon execution, making it even more suitable for DTMF control.

## Usage

To use the `SkyControl.py` script, you need to call it with two parameters:

1. The name of the setting you want to change (case insensitive).

   - Enable (Completely enable/disable SkywarnPlus)
   - SayAlert
   - SayAllClear
   - TailMessage
   - CourtesyTone
   - IDChange
   - AlertScript

2. The new value for the setting (either 'true' or 'false' or 'toggle').

For example, to completely disable SkywarnPlus, you would use:

```bash
/usr/local/bin/SkywarnPlus/SkyControl.py enable false
```

And to reenable it, you would use:

```bash
/usr/local/bin/SkywarnPlus/SkyControl.py enable true
```

And to toggle it, you would use:

```bash
/usr/local/bin/SkywarnPlus/SkyControl.py enable toggle
```

You can also use `SkyControl.py` to manually force the state of Courtesy Tones or IDs:

```bash
/usr/local/bin/SkywarnPlus/SkyControl.py changect normal
/usr/local/bin/SkywarnPlus/SkyControl.py changect wx
/usr/local/bin/SkywarnPlus/SkyControl.py changeid normal
/usr/local/bin/SkywarnPlus/SkyControl.py changect wx
```

## Spoken Feedback

Upon the successful execution of a control command, the `SkyControl.py` script will provide spoken feedback that corresponds to the change made. For instance, if you execute a command to enable the SayAlert function, the script will play an audio message stating that SayAlert has been enabled. This feature enhances user experience and confirms that the desired changes have been effected.

## Mapping to DTMF Commands

You can map the `SkyControl.py` script to DTMF commands in the `rpt.conf` file of your node. Here is an example of how to do this:

```bash
801 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py enable toggle ; Toggles SkywarnPlus
802 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py sayalert toggle ; Toggles SayAlert
803 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py sayallclear toggle ; Toggles SayAllClear
804 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py tailmessage toggle ; Toggles TailMessage
805 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py courtesytone toggle ; Toggles CourtesyTone
806 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py alertscript toggle ; Toggles AlertScript
807 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py idchange toggle ; Toggles IDChange
808 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py changect normal ; Forces CT to "normal" mode
809 = cmd,/usr/local/bin/SkywarnPlus/SkyControl.py changeid normal ; Forces ID to "normal" mode
```

With this setup, you can control SkywarnPlus' functionality using DTMF commands.

# AlertScript

SkywarnPlus's `AlertScript` feature is an immensely flexible tool that provides the ability to program your node to respond to specific alerts in unique ways. By enabling you to map alerts to DTMF commands or bash scripts, `AlertScript` offers you the versatility to design your own extensions to SkywarnPlus, modifying its functionalities to perfectly fit your needs.

With `AlertScript`, you can outline actions to be executed when specific alerts are activated. For instance, you might want to broadcast a unique sound, deliver a particular message, or initiate any other action your hardware can perform and that can be activated by a DTMF command or bash script.

## Understanding AlertScript

To utilize `AlertScript`, you define the mapping of alerts to either DTMF commands or bash scripts in the `config.yaml` file under the `AlertScript` section.

Here are examples of how to map alerts to DTMF commands or bash scripts:

```yaml
AlertScript:
  Enable: true
  Mappings:
    - Type: DTMF
      Nodes:
        - <NODE_NUMBERS>
      Commands:
        - '<DTMF_COMMAND>'
      Triggers: 
        - <ALERTS>
      Match: ALL # or ANY
    - Type: BASH
      Commands:
        - '<BASH_COMMAND>'
      Triggers: 
        - <ALERTS>
```

In the examples above, `<NODE_NUMBERS>` are the nodes where you want the DTMF command to be dispatched, `<DTMF_COMMAND>` is the command to be executed, and `<ALERTS>` are the alerts to trigger this command. Likewise, for bash commands, `<BASH_COMMAND>` is the script to be executed and `<ALERTS>` are the alerts to trigger this script. Note that wildcards (`*`) can be used in `<ALERTS>` for broader matches.

## The Power of YOU

`AlertScript` derives its power from its versatility and extensibility. By providing the capacity to directly interface with your node's functionality through DTMF commands or bash scripts, you can effectively program the node to do virtually anything in response to a specific weather alert.

Fancy activating a siren when a tornado warning is received? You can do that. Want to send an email notification when there's a severe thunderstorm warning? You can do that too. The only limit is the capability of your node and connected systems.

In essence, `AlertScript` unleashes a world of customization possibilities, empowering you to add new capabilities to SkywarnPlus, create your own extensions, and modify your setup to align with your specific requirements and preferences. By giving you the authority to dictate how your system should react to various weather alerts, `AlertScript` makes SkywarnPlus a truly powerful tool for managing weather alerts on your node.

# Customizing the Audio Files

SkywarnPlus comes with a library of audio files that can be replaced with any 8kHz mono PCM16 WAV files you want. These are found in the `SOUNDS/` directory by default, along with `DICTIONARY.txt` which explains audio file assignments.

If you'd like to enable IDChange, you must create your own ID audio files. Follow **[this guide](https://wiki.allstarlink.org/images/d/dd/RecordingSoundFiles.pdf)** on how to create audio files for use with Asterisk/app_rpt.

# Testing

SkywarnPlus provides the ability to inject predefined alerts, bypassing the call to the NWS API. This feature is extremely useful for testing SkywarnPlus.

To enable this option, modify the following settings in the `[DEV]` section of your `config.yaml` file:

```yaml
# Enable test alert injection instead of calling the NWS API by setting 'INJECT' to 'True'.
INJECT: false
# List the test alerts to inject. Use a case-sensitive list. One alert per line for better readability.
INJECTALERTS:
   - Tornado Warning
   - Tornado Watch
   - Severe Thunderstorm Warning
```

# Debugging

Debugging is an essential part of diagnosing issues with SkywarnPlus. To facilitate this, SkywarnPlus provides a built-in debugging feature. Here's how to use it:

1. **Enable Debugging**: The debugging feature can be enabled in the `config.yaml` file. Open this file and set the `debug` option under the `[SkywarnPlus]` section to `true`.

```yaml
Logging:
  # Configuration for logging options.
  # Enable verbose logging by setting 'Debug' to 'True'.
  Debug: false
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

If the spare time I put into the development of SkywarnPlus has helped you, please consider supporting!

<center><a href="https://www.paypal.com/donate/?business=93AJFB9BAVSJL&no_recurring=0&item_name=Thank+you+so+much+for+your+support%21+I+put+a+lot+of+my+spare+time+into+this%2C+and+I+sincerely+appreciate+YOU%21&currency_code=USD">
  <img src="https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png" width=300px alt="Donate with PayPal" />
</a></center>

# License

SkywarnPlus is open-sourced software licensed under the [MIT license](LICENSE).

Created by Mason Nelson (N5LSN/WRKF394)

Audio Library voiced by Rachel Nelson