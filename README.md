# Sunshine Game Stream for Home Assistant

A Home Assistant custom integration that monitors your LizardByte Sunshine game streaming server and detects active streaming sessions in real-time.

> **Note:** This integration was created and reviewed with the help of LLM. It has been tested but use at your own risk.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Method 1: Direct Download](#method-1-direct-download)
  - [Method 2: Git Clone](#method-2-git-clone)
- [Configuration](#configuration)
- [Usage](#usage)
  - [In Automations](#in-automations)
  - [In Dashboards](#in-dashboards)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [Contributing](#contributing)
- [License](#license)

## Overview

This integration connects to your [LizardByte Sunshine](https://github.com/LizardByte/Sunshine) game streaming server and creates a sensor that shows whether someone is actively streaming. It monitors Sunshine's logs in real-time to detect streaming sessions, allowing you to trigger automations, control lights, manage power, and more based on your gaming activity.

**Perfect for:**
- Automating your gaming environment (lights, speakers, displays)
- Preventing PC shutdown during active streaming sessions
- Tracking gaming activity and usage statistics
- Creating presence detection based on streaming status
- Building smart home routines around your gaming setup

## Features

- ✅ **Real-time streaming detection** - Know instantly when streaming starts/stops
- ✅ **UI-based configuration** - Easy setup through Home Assistant interface
- ✅ **Multiple server support** - Monitor multiple Sunshine servers simultaneously
- ✅ **Optional authentication** - Works with or without Sunshine credentials
- ✅ **Configurable update interval** - Adjust polling frequency (default: 2 seconds)
- ✅ **Custom server naming** - Give each server a friendly name
- ✅ **Device integration** - Shows up as a device with model/version info
- ✅ **Dynamic icons** - Visual feedback when streaming is active
- ✅ **No performance impact** - Uses INFO level logs only
- ✅ **Multilingual** - English and French translations included

## Prerequisites

- **Home Assistant** 2023.1 or newer
- **LizardByte Sunshine** - Running on your gaming PC
  - Download from: [https://github.com/LizardByte/Sunshine](https://github.com/LizardByte/Sunshine)
- **Network access** from Home Assistant to Sunshine web UI (default port: 47990)
- **Optional:** Sunshine authentication credentials (if enabled in your setup)

## Installation

### Method 1: Direct Download

1. Download the latest release from [Releases](https://github.com/spyspirit0/sunshine-gamestream-ha/releases)

2. Extract the files and copy the `sunshine_gamestream` folder to your Home Assistant `custom_components` directory:
```
   /config/custom_components/sunshine_gamestream/
```

3. Your directory structure should look like:
```
   /config/custom_components/sunshine_gamestream/
   ├── __init__.py
   ├── config_flow.py
   ├── sensor.py
   ├── manifest.json
   ├── strings.json
   └── translations/
       ├── en.json
       └── fr.json
```

4. Restart Home Assistant

5. Continue to [Configuration](#configuration)

### Method 2: Git Clone

1. Navigate to your Home Assistant custom_components directory:
```bash
   cd /config/custom_components/
```

2. Clone the repository:
```bash
   git clone https://github.com/spyspirit0/sunshine-gamestream-ha.git sunshine_gamestream
```

3. Restart Home Assistant

4. Continue to [Configuration](#configuration)

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ ADD INTEGRATION"** (bottom right)
3. Search for **"LizardByte Sunshine"**
4. Click on it to open the configuration form

### Configuration Options

Fill in the following details:

**Required:**
- **Server Name** - A friendly name for this server (e.g., "Gaming PC", "Living Room PC")
- **Host IP Address** - Your PC's IP address where Sunshine is running (e.g., `192.168.1.100`)
- **Port** - Sunshine web UI port (default: `47990`)

**Optional:**
- **Username** - Leave empty if authentication is not enabled on your Sunshine server
- **Password** - Leave empty if authentication is not enabled on your Sunshine server
- **Update interval (seconds)** - How often to check for streaming status (default: `2`)

### Finding Your Sunshine IP and Port

1. On your gaming PC, open the Sunshine web UI
2. The URL will be something like `https://192.168.1.100:47990`
3. Use the IP address (`192.168.1.100`) and port (`47990`) in the integration config

### Authentication Setup

**If Sunshine has no password:**
- Leave username and password fields empty

**If Sunshine requires authentication:**
1. Go to Sunshine Web UI → Settings → Configuration → Web UI
2. Note your configured username and password
3. Enter these credentials in the integration setup

## Usage

### Sensor Entity

After configuration, you'll get a sensor entity:
- **Entity ID:** `sensor.[server_name]_sunshine_status`
- **States:**
  - `idle` - No active streaming session
  - `streaming` - Someone is currently streaming
  - `unavailable` - Cannot connect to Sunshine server

### In Automations

#### Example 1: Turn on RGB lighting when streaming starts
```yaml
automation:
  - alias: "Gaming Mode - Lights On"
    trigger:
      - platform: state
        entity_id: sensor.gaming_pc_sunshine_status
        to: "streaming"
    action:
      - service: light.turn_on
        target:
          entity_id: light.desk_rgb
        data:
          brightness: 255
          rgb_color: [0, 255, 0]
```

#### Example 2: Prevent PC shutdown during streaming
```yaml
automation:
  - alias: "Block Shutdown While Streaming"
    trigger:
      - platform: event
        event_type: call_service
        event_data:
          domain: switch
          service: turn_off
          service_data:
            entity_id: switch.gaming_pc
    condition:
      - condition: state
        entity_id: sensor.gaming_pc_sunshine_status
        state: "streaming"
    action:
      - service: notify.mobile_app
        data:
          title: "Cannot shutdown PC"
          message: "Gaming session is active!"
```

#### Example 3: Auto-disable notifications while gaming
```yaml
automation:
  - alias: "DND Mode When Streaming"
    trigger:
      - platform: state
        entity_id: sensor.gaming_pc_sunshine_status
        to: "streaming"
    action:
      - service: notify.mobile_app
        data:
          message: "command_dnd"
          data:
            command: "on"
  
  - alias: "Enable Notifications After Gaming"
    trigger:
      - platform: state
        entity_id: sensor.gaming_pc_sunshine_status
        from: "streaming"
        to: "idle"
    action:
      - service: notify.mobile_app
        data:
          message: "command_dnd"
          data:
            command: "off"
```

#### Example 4: Track gaming sessions
```yaml
automation:
  - alias: "Log Gaming Session Start"
    trigger:
      - platform: state
        entity_id: sensor.gaming_pc_sunshine_status
        to: "streaming"
    action:
      - service: logbook.log
        data:
          name: "Gaming Session"
          message: "Started gaming on {{ trigger.to_state.attributes.friendly_name }}"
  
  - alias: "Log Gaming Session End"
    trigger:
      - platform: state
        entity_id: sensor.gaming_pc_sunshine_status
        from: "streaming"
        to: "idle"
        for: "00:00:10"
    action:
      - service: logbook.log
        data:
          name: "Gaming Session"
          message: "Gaming session ended after {{ relative_time(trigger.from_state.last_changed) }}"
```

### In Dashboards

#### Simple Entity Card
```yaml
type: entity
entity: sensor.gaming_pc_sunshine_status
name: Gaming PC Status
icon: mdi:controller
```

#### Conditional Card (Shows Only When Streaming)
```yaml
type: conditional
conditions:
  - entity: sensor.gaming_pc_sunshine_status
    state: streaming
card:
  type: markdown
  content: |
    ## 🎮 Gaming Session Active
    Someone is streaming from the Gaming PC
```

#### Multiple Servers
```yaml
type: entities
title: Game Streaming Status
entities:
  - sensor.gaming_pc_sunshine_status
  - sensor.living_room_pc_sunshine_status
  - sensor.bedroom_pc_sunshine_status
```

## Troubleshooting

### Cannot Find Integration in Home Assistant

**Symptoms:** "LizardByte Sunshine" doesn't appear when adding integrations

**Solutions:**
- Verify all files are in `/config/custom_components/sunshine_gamestream/`
- Check file permissions (files should be readable)
- Restart Home Assistant completely
- Check Home Assistant logs: **Settings** → **System** → **Logs** → Search "sunshine"
- Look for Python import errors or missing dependencies

### Connection Errors

**Error:** `Failed to connect to Sunshine server`

**Solutions:**
- Verify Sunshine is running on your gaming PC
- Test the Sunshine web UI in your browser: `https://[YOUR_IP]:47990`
- Check that port 47990 is accessible from Home Assistant
- Verify firewall settings on your gaming PC
- Ensure the IP address in the integration config is correct
- Try using the PC's hostname instead of IP address

### Authentication Errors

**Error:** `Invalid username or password`

**Solutions:**
- Verify credentials by logging into Sunshine web UI manually
- If Sunshine has no authentication, leave username/password empty
- Check for extra spaces when copying credentials
- Ensure authentication is enabled in Sunshine if you're providing credentials

### Sensor Shows "Unavailable"

**Symptoms:** Sensor exists but shows as unavailable

**Solutions:**
- Check Home Assistant logs for specific error messages
- Verify Sunshine's `/api/logs` endpoint is accessible:
  - Open in browser: `https://[YOUR_IP]:47990/api/logs`
  - You should see log content (might need to accept SSL certificate)
- Check network connectivity between Home Assistant and Sunshine
- Try removing and re-adding the integration
- Verify Sunshine service is running on the PC

### Streaming Not Detected

**Symptoms:** You're streaming but sensor stays on "idle"

**Solutions:**
- Check that Sunshine is actually streaming (look at Sunshine logs)
- Verify your Sunshine log level is at least "Info":
  - Go to Sunshine Web UI → Configuration → Advanced
  - Set "Minimum Log Level" to "Info" or "Debug"
- Check Home Assistant logs for pattern matching errors
- Test manually: Start streaming and check Sunshine logs for "CLIENT CONNECTED"
- Ensure you're using a recent version of Sunshine (older versions may use different log formats)

### Slow Updates or Delays

**Symptoms:** Takes a long time for state to change

**Solutions:**
- Check your configured scan interval (default is 2 seconds)
- Verify network latency between Home Assistant and Sunshine
- Look for errors in Home Assistant logs
- Try increasing the scan interval if you have network issues
- Remove and re-add the integration to reset the coordinator

### SSL Certificate Warnings

**Symptoms:** Browser warnings about self-signed certificates

**Note:** This is normal! Sunshine uses self-signed SSL certificates.

**Solutions:**
- The integration handles this automatically
- You can safely ignore these warnings
- If using curl/wget for testing, add `-k` or `--insecure` flag

## Technical Details

### How It Works

1. **Polling:** The integration polls Sunshine's `/api/logs` endpoint at your configured interval (default: 2 seconds)
2. **Log Analysis:** It searches log content for specific patterns that indicate streaming activity
3. **Pattern Matching:** Detects "CLIENT CONNECTED" and "CLIENT DISCONNECTED" messages
4. **State Updates:** Changes sensor state between `idle` and `streaming` when patterns are detected
5. **Efficient Updates:** Only checks new log entries since last poll to minimize processing

### Log Patterns Used

**Streaming Start:**
- `CLIENT CONNECTED`
- `New streaming session started`

**Streaming Stop:**
- `CLIENT DISCONNECTED`

### API Endpoints Used

- **GET /api/config** - Initial connection test and Sunshine version detection
- **GET /api/logs** - Continuous monitoring for streaming events

### Performance Impact

**On Home Assistant:**
- Network: Minimal (small HTTP request every 2 seconds)
- CPU: Very low (simple text pattern matching)
- Memory: Minimal (stores only last log line for comparison)

**On Sunshine:**
- No performance impact (uses INFO level logs, not DEBUG/VERBOSE)
- No configuration changes made automatically
- Read-only access to logs endpoint

### Data Privacy

- All communication happens locally on your network
- No cloud services or external connections
- Credentials are stored encrypted in Home Assistant's configuration
- Only accesses Sunshine's public API endpoints

## Contributing

Contributions are welcome! Here's how you can help:

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly on your own setup
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow Home Assistant's integration standards
- Maintain backward compatibility when possible
- Update translations for new strings
- Add tests for new functionality
- Document all configuration options

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration modifies no settings on your Sunshine server and operates in read-only mode. However, it is provided as-is without warranty. Always ensure you have backups of your Home Assistant configuration.

The integration monitors Sunshine's logs to detect streaming activity. While it has been tested with various Sunshine versions, log formats may change in future releases.

## Acknowledgments

- Created and reviewed with assistance from Claude (Anthropic)
- Thanks to the [LizardByte](https://github.com/LizardByte) team for creating Sunshine
- Inspired by the Home Assistant community's automation needs
- Icon graphics from [Material Design Icons](https://pictogrammers.com/library/mdi/)

## Support

### Getting Help

If you need assistance:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review [Sunshine's documentation](https://docs.lizardbyte.dev/projects/sunshine/latest/)
3. Search existing [GitHub Issues](https://github.com/spyspirit0/sunshine-gamestream-ha/issues)
4. Create a new issue with detailed information

### Useful Links

- **Integration Repository:** [https://github.com/spyspirit0/sunshine-gamestream-ha](https://github.com/spyspirit0/sunshine-gamestream-ha)
- **Sunshine Project:** [https://github.com/LizardByte/Sunshine](https://github.com/LizardByte/Sunshine)
- **Sunshine Documentation:** [https://docs.lizardbyte.dev/projects/sunshine/latest/](https://docs.lizardbyte.dev/projects/sunshine/latest/)
- **Home Assistant Community:** [https://community.home-assistant.io/](https://community.home-assistant.io/)

---

**Made with ❤️ for the Home Assistant and game streaming community**