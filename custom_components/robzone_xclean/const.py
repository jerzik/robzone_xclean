"""Constants for Robzone Duoro Xclean LAN integration."""
from __future__ import annotations

DOMAIN = "robzone_xclean"
VERSION = "2.1.0"

CONF_AUTH_CODE = "auth_code"
CONF_TARGET_ID = "target_id"

DEFAULT_PORT = 8888
DEFAULT_VERSION = "5.0.8"
DEFAULT_TARGET_TYPE = "3"
DEFAULT_SCAN_INTERVAL_SECONDS = 60

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

    # Suction power control verified for the HCTRobot protocol family.
    # 1 = off, 2 = normal, 3 = turbo/MAX, 4 = eco.
    "fan_off": {"fan": "1", "transitCmd": "110"},
    "fan_normal": {"fan": "2", "transitCmd": "110"},
    "normal": {"fan": "2", "transitCmd": "110"},
    "fan_max": {"fan": "3", "transitCmd": "110"},
    "max": {"fan": "3", "transitCmd": "110"},
    "turbo": {"fan": "3", "transitCmd": "110"},
    "fan_eco": {"fan": "4", "transitCmd": "110"},
    "eco": {"fan": "4", "transitCmd": "110"},

    # Manual movement verified from RobZone app protocol family
    "forward": {"direction": "1", "transitCmd": "108"},
    "dopredu": {"direction": "1", "transitCmd": "108"},
    "left": {"direction": "3", "transitCmd": "108"},
    "doleva": {"direction": "3", "transitCmd": "108"},
    "right": {"direction": "4", "transitCmd": "108"},
    "manual_stop": {"direction": "5", "tag": "5", "transitCmd": "108"},
    "stop_move": {"direction": "5", "tag": "5", "transitCmd": "108"},
    "doprava": {"direction": "4", "transitCmd": "108"},
    "back": {"direction": "2", "transitCmd": "108"},
    "backward": {"direction": "2", "transitCmd": "108"},
    "dozadu": {"direction": "2", "transitCmd": "108"},

    # Live map / track query verified from PCAPdroid captures.
    # Response is transitCmd 132 and includes clearArea, clearTime, clearSign,
    # map and track as Base64 encoded binary payloads.
    "map": {"total": "", "transitCmd": "131"},
    "keepalive": {"total": "", "transitCmd": "131"},
    "get_map": {"total": "", "transitCmd": "131"},
}
