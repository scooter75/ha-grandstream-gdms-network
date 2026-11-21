# Grandstream GDMS Networking for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Home Assistant Marketplace custom integration for **Grandstream GDMS Networking** (`gdms.cloud` / `gwn.cloud`) using the official Grandstream GWN OpenAPI (`v1.0.0`).

## Features

- **OAuth 2.0 & SHA-256 Request Signing**: Automatically manages `client_credentials` token refreshes and request signatures.
- **Network Telemetry Sensors**: Tracks total access points, online access points, and total connected clients per network.
- **Per-Access-Point Diagnostics**: Monitors client counts, IP addresses, firmware versions, and active 2.4 GHz / 5 GHz channels.
- **Wi-Fi Client Presence (`device_tracker`)**: Automatic presence detection for connected wireless and wired clients with RSSI, SSID, link rate, and connected AP metadata.

---

## Prerequisites: Enable API Developer Mode in GDMS

1. Log in to your **Grandstream GDMS** portal (`https://www.gdms.cloud` for Global/US or `https://eu.gdms.cloud` for Europe) and switch to **Networking**.
2. In the left navigation sidebar, go to **System > API Developer** (or **API Developer** on the main menu).
3. Click **Apply for API Developer** / **Enable API Developer Mode**.
4. Copy your assigned **Client ID (App ID)** and **Secret Key**.

---

## Installation

### Option 1: Home Assistant Marketplace (Recommended)

1. Open Home Assistant and navigate to **Settings > Marketplace** (or **HACS** on Home Assistant `< 2026.11`).
2. Click the three-dots menu in the top-right corner and select **Custom repositories**.
3. Enter the repository URL `https://github.com/scooter75/ha-grandstream-gdms`, choose **Integration** as the type, and click **Add**.
4. Locate **Grandstream GDMS Networking** in the Marketplace list and click **Download / Install**.
5. Restart Home Assistant if prompted.

### Option 2: Manual Installation

1. Copy the `custom_components/grandstream_gdms` directory into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings > Devices & services** and click **+ Add integration**.
2. Search for **Grandstream GDMS Networking**.
3. Select your **GDMS / GWN Server Region** and enter your **API Client / App ID** and **API Secret Key**.
4. Choose the **Network / Site** you wish to monitor and click **Submit**.

To adjust the polling interval (default: `60` seconds), open the integration entry under **Settings > Devices & services > Grandstream GDMS Networking** and click **Configure**.

---

## Usage Examples

### Presence Automation (Turn Off Lights When Everyone Leaves Wi-Fi)

```yaml
automation:
  - alias: "Turn off office lights when phone disconnects from GWN Wi-Fi"
    trigger:
      - platform: state
        entity_id: device_tracker.work_phone
        from: "home"
        to: "not_home"
        for:
          minutes: 3
    action:
      - service: light.turn_off
        target:
          area_id: office
```

### Alert When an Access Point Goes Offline

```yaml
automation:
  - alias: "Alert when Grandstream AP drops offline"
    trigger:
      - platform: numeric_state
        entity_id: sensor.gdms_main_office_online_access_points
        below: 3
    action:
      - service: notify.mobile_app_admin_phone
        data:
          title: "Grandstream Network Alert"
          message: >
            Online AP count dropped to {{ states('sensor.gdms_main_office_online_access_points') }}
            out of {{ states('sensor.gdms_main_office_total_access_points') }}.
```

### Lovelace Network Overview Card

```yaml
type: entities
title: Grandstream GDMS Network
entities:
  - entity: sensor.gdms_main_office_online_access_points
    name: Online Access Points
  - entity: sensor.gdms_main_office_total_access_points
    name: Total Access Points
  - entity: sensor.gdms_main_office_connected_clients
    name: Active Wi-Fi Clients
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
