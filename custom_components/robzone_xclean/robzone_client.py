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
        # The robot firmware accepts only one LAN session reliably. Serialize
        # coordinator polling, dashboard commands and automations.
        self._command_lock = asyncio.Lock()
        self._last_command_finished = 0.0

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

        status_keys = (
            "battery",
            "workState",
            "workMode",
            "fan",
            "direction",
            "error",
        )
        if any(k in value for k in status_keys):
            # The HCT handshake sometimes returns a placeholder status where
            # every field is "0". It must not replace the last valid status.
            present = [str(value[k]) for k in status_keys if k in value]
            if present and all(item == "0" for item in present):
                return
            self.last_status.update(value)

    def _status_from_objects(
        self, objects: list[dict[str, Any]]
    ) -> RobzoneStatus | None:
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
        """Serialize and send a command to the vacuum."""
        async with self._command_lock:
            loop = asyncio.get_running_loop()
            cooldown = 2.0 - (loop.time() - self._last_command_finished)
            if cooldown > 0:
                await asyncio.sleep(cooldown)
            try:
                return await self._send_command_unlocked(command)
            finally:
                self._last_command_finished = loop.time()

    async def _open_connection(
        self,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open the LAN socket, retrying only before a command is sent."""
        last_error: OSError | None = None
        for attempt in range(3):
            try:
                return await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self.timeout,
                )
            except OSError as exc:
                last_error = exc
                if attempt == 2:
                    raise
                await asyncio.sleep(1.5 * (attempt + 1))
        raise last_error or ConnectionError("Robzone connection failed")

    async def _send_command_unlocked(
        self, command: str
    ) -> RobzoneStatus | None:
        """Send one command while holding the client command lock."""
        packet = self._build_packet(command)

        reader: asyncio.StreamReader | None = None
        writer: asyncio.StreamWriter | None = None

        try:
            reader, writer = await self._open_connection()

            writer.write(HANDSHAKE)
            await writer.drain()

            try:
                handshake_response = await asyncio.wait_for(
                    reader.read(4096), timeout=2.0
                )
                if handshake_response:
                    _LOGGER.debug(
                        "Robzone handshake response: %s",
                        handshake_response.hex(" "),
                    )
                    handshake_objects = self._extract_json_objects(handshake_response)
                    if handshake_objects:
                        self._status_from_objects(handshake_objects)
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.25)

            writer.write(packet)
            await writer.drain()

            chunks: list[bytes] = []
            loop = asyncio.get_running_loop()
            deadline = loop.time() + 3.0
            quiet_deadline: float | None = None

            # A connection can deliver an acknowledgement, old status and then
            # post-command status. Wait until it becomes quiet so the newest
            # status wins instead of lagging one command behind.
            while True:
                now = loop.time()
                remaining = deadline - now
                if quiet_deadline is not None:
                    remaining = min(remaining, quiet_deadline - now)
                if remaining <= 0:
                    break

                try:
                    chunk = await asyncio.wait_for(reader.read(8192), timeout=remaining)
                except asyncio.TimeoutError:
                    break

                if not chunk:
                    break

                chunks.append(chunk)
                quiet_deadline = loop.time() + 0.8

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

