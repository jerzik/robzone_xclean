"""LAN TCP client for Robzone Duoro Xclean / HCTRobot compatible vacuums."""
from __future__ import annotations

import asyncio
import json
import logging
import struct
from dataclasses import dataclass, field
from json import JSONDecoder
from typing import Any

from .const import COMMANDS, DEFAULT_TARGET_TYPE, DEFAULT_VERSION

_LOGGER = logging.getLogger(__name__)

HANDSHAKE = bytes.fromhex(
    "14 00 00 00 00 01 c8 00 00 00 01 00 16 27 00 00 00 00 00 00"
)

HEADER_TAIL = bytes.fromhex(
    "fa 00 c8 00 00 00 19 27 18 27 00 00 00 00 00 00"
)


@dataclass
class RobzoneStatus:
    """Parsed status returned by the vacuum."""

    raw: dict[str, Any] = field(default_factory=dict)
    battery: int | None = None
    work_state: str | None = None
    work_mode: str | None = None
    fan: str | None = None
    direction: str | None = None
    error: str | None = None
    clear_area: str | None = None
    clear_time: str | None = None
    clear_sign: str | None = None
    map_raw: str | None = None
    track_raw: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RobzoneStatus":
        """Create RobzoneStatus from raw JSON payload."""
        value = payload.get("value", {}) if isinstance(payload, dict) else {}

        battery_raw = value.get("battery")
        try:
            battery = int(battery_raw) if battery_raw is not None else None
        except (TypeError, ValueError):
            battery = None

        return cls(
            raw=payload,
            battery=battery,
            work_state=value.get("workState"),
            work_mode=value.get("workMode"),
            fan=value.get("fan"),
            direction=value.get("direction"),
            error=value.get("error"),
            clear_area=value.get("clearArea"),
            clear_time=value.get("clearTime"),
            clear_sign=value.get("clearSign"),
            map_raw=value.get("map"),
            track_raw=value.get("track"),
        )


class RobzoneClient:
    """Small TCP client for the local port 8888 protocol."""

    def __init__(
        self,
        host: str,
        port: int,
        auth_code: str,
        target_id: str,
        *,
        version: str = DEFAULT_VERSION,
        target_type: str = DEFAULT_TARGET_TYPE,
        timeout: float = 5.0,
    ) -> None:
        """Initialize Robzone client."""
        self.host = host
        self.port = int(port)
        self.auth_code = str(auth_code)
        self.target_id = str(target_id)
        self.version = version
        self.target_type = target_type
        self.timeout = timeout

        self.last_status: dict[str, Any] = {}
        self.last_map: dict[str, Any] = {}

    def _build_packet(self, command: str) -> bytes:
        """Build binary packet with JSON payload."""
        command_key = command.lower().strip()

        if command_key not in COMMANDS:
            raise ValueError(f"Unknown Robzone command: {command}")

        data = {
            "cmd": "0",
            "control": {
                "authCode": self.auth_code,
                "deviceIp": self.host,
                "devicePort": str(self.port),
                "targetId": self.target_id,
                "targetType": self.target_type,
            },
            "seq": "0",
            "value": COMMANDS[command_key],
            "version": self.version,
        }

        json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
        total_len = 20 + len(json_bytes)

        return struct.pack("<I", total_len) + HEADER_TAIL + json_bytes

    @staticmethod
    def _extract_json_objects(raw: bytes) -> list[dict[str, Any]]:
        """Extract JSON objects from binary response."""
        text = raw.decode("utf-8", errors="ignore")
        decoder = JSONDecoder()
        objects: list[dict[str, Any]] = []

        start = 0
        while True:
            start = text.find("{", start)
            if start == -1:
                break

            try:
                obj, end = decoder.raw_decode(text[start:])
            except ValueError:
                start += 1
                continue

            if isinstance(obj, dict):
                objects.append(obj)

            start += end

        return objects

    def _save_status_payload(self, payload: dict[str, Any]) -> None:
        """Save status/map payload values."""
        value = payload.get("value", {}) if isinstance(payload, dict) else {}
        if not isinstance(value, dict):
            return

        if value.get("transitCmd") == "132" or "map" in value or "track" in value:
            self.last_map = dict(value)
            # Also expose map statistics in last_status for dashboard/template use.
            for key in ("clearArea", "clearTime", "clearModule", "clearSign"):
                if key in value:
                    self.last_status[key] = value[key]
            return

        if any(k in value for k in ("battery", "workState", "workMode", "fan", "direction", "error")):
            self.last_status.update(value)

    def _status_from_objects(self, objects: list[dict[str, Any]]) -> RobzoneStatus | None:
        """Process all parsed objects and return the last useful status."""
        useful: RobzoneStatus | None = None

        for obj in objects:
            self._save_status_payload(obj)
            value = obj.get("value", {}) if isinstance(obj, dict) else {}
            if isinstance(value, dict):
                if any(
                    key in value
                    for key in (
                        "battery",
                        "workState",
                        "workMode",
                        "error",
                        "clearArea",
                        "clearTime",
                        "map",
                        "track",
                    )
                ):
                    useful = RobzoneStatus.from_payload(obj)

        return useful

    async def send_command(self, command: str) -> RobzoneStatus | None:
        """Send command to vacuum and return parsed status."""
        packet = self._build_packet(command)

        reader: asyncio.StreamReader | None = None
        writer: asyncio.StreamWriter | None = None

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )

            writer.write(HANDSHAKE)
            await writer.drain()

            try:
                handshake_response = await asyncio.wait_for(reader.read(4096), timeout=2.0)
                if handshake_response:
                    _LOGGER.debug("Robzone handshake response: %s", handshake_response.hex(" "))
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.25)

            writer.write(packet)
            await writer.drain()

            chunks: list[bytes] = []
            deadline = asyncio.get_running_loop().time() + 2.0

            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    break

                try:
                    chunk = await asyncio.wait_for(reader.read(8192), timeout=remaining)
                except asyncio.TimeoutError:
                    break

                if not chunk:
                    break

                chunks.append(chunk)

                joined = b"".join(chunks)
                # Status/map payloads usually arrive quickly. For map responses,
                # wait until map/track appears, otherwise return after value.
                if command in ("map", "get_map"):
                    if b'"track"' in joined or b'"map"' in joined:
                        break
                elif b'"value"' in joined:
                    break

            raw = b"".join(chunks)
            objects = self._extract_json_objects(raw)

            if objects:
                return self._status_from_objects(objects)

            if raw:
                _LOGGER.debug("Robzone response without parsed JSON: %s", raw.hex(" "))

            return None

        finally:
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:  # noqa: BLE001
                    pass

    async def async_send_command(self, command: str) -> RobzoneStatus | None:
        """Home Assistant friendly command alias."""
        return await self.send_command(command)

    async def async_get_map(self) -> RobzoneStatus | None:
        """Fetch current live map/track payload from the vacuum."""
        return await self.send_command("map")
