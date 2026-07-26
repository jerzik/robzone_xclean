"""Constants for Robzone Duoro Xclean LAN integration."""
from __future__ import annotations

DOMAIN = "robzone_xclean"
VERSION = "2.0.0"

CONF_AUTH_CODE = "auth_code"
CONF_TARGET_ID = "target_id"

DEFAULT_PORT = 8888
DEFAULT_VERSION = "5.0.8"
DEFAULT_TARGET_TYPE = "3"
DEFAULT_SCAN_INTERVAL_SECONDS = 15

COMMANDS = {
    # Basic cleaning commands
    "start": {"start": "1", "transitCmd": "100"},
    "pause": {"pause": "1", "transitCmd": "102"},
    "stop": {"pause": "1", "transitCmd": "102"},
    "dock": {"charge": "1", "transitCmd": "104"},
    "charge": {"charge": "1", "transitCmd": "104"},
    "home": {"charge": "1", "transitCmd": "104"},

    # Cleaning modes verified from PCAPdroid captures
    "auto": {"mode": "6", "transitCmd": "106"},
    "podel_zdi": {"mode": "4", "transitCmd": "106"},
    "edge": {"mode": "4", "transitCmd": "106"},
    "wall": {"mode": "4", "transitCmd": "106"},
    "spot": {"mode": "1", "transitCmd": "106"},

    # Manual movement verified from RobZone app protocol family
    "forward": {"direction": "1", "transitCmd": "108"},
    "dopredu": {"direction": "1", "transitCmd": "108"},
    "left": {"direction": "3", "transitCmd": "108"},
    "doleva": {"direction": "3", "transitCmd": "108"},
    "right": {"direction": "4", "transitCmd": "108"},
    "manual_stop": {"direction": "5", "tag": "5", "transitCmd": "108"},
    "stop_move": {"direction": "5", "tag": "5", "transitCmd": "108"},
    "doprava": {"direction": "4", "transitCmd": "108"},
    "back": {"direction": "5", "tag": "5", "transitCmd": "108"},
    "backward": {"direction": "5", "transitCmd": "108"},
    "dozadu": {"direction": "5", "transitCmd": "108"},

    # Live map / track query verified from PCAPdroid captures.
    # Response is transitCmd 132 and includes clearArea, clearTime, clearSign,
    # map and track as Base64 encoded binary payloads.
    "map": {"total": "", "transitCmd": "131"},
    "keepalive": {"total": "", "transitCmd": "131"},
    "get_map": {"total": "", "transitCmd": "131"},
}
