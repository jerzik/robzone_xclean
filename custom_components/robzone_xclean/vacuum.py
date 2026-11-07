"""Vacuum platform for Robzone Duoro Xclean LAN."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

FAN_VALUE_TO_SPEED = {
    "1": "off",
    "2": "normal",
    "3": "max",
    "4": "eco",
}

FAN_SPEED_TO_ACTION = {
    "off": "fan_off",
    "normal": "fan_normal",
    "max": "fan_max",
    "turbo": "fan_max",
    "eco": "fan_eco",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Robzone vacuum entity from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [RobzoneXcleanVacuum(entry, data["client"], data["coordinator"])],
        True,
    )


class RobzoneXcleanVacuum(StateVacuumEntity):
    """Robzone Duoro Xclean LAN vacuum entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:robot-vacuum"

    _attr_supported_features = (
        VacuumEntityFeature.STATE
        | VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.FAN_SPEED
    )
    _attr_fan_speed_list = ["off", "normal", "max", "eco"]

    def __init__(self, entry: ConfigEntry, client: Any, coordinator: Any) -> None:
        """Initialize entity."""
        self._entry = entry
        self._client = client
        self._coordinator = coordinator

        self._attr_unique_id = f"{entry.entry_id}_vacuum"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title or "Robzone Duoro Xclean 5",
            "manufacturer": "Robzone / HCTRobot compatible",
            "model": "Duoro Xclean 5",
            "configuration_url": f"http://{entry.data.get('host', '')}",
        }

        self._attr_activity = VacuumActivity.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {}
        status = getattr(self._client, "last_status", {})
        map_data = getattr(self._client, "last_map", {})

        if isinstance(status, dict):
            attrs.update(status)

        if isinstance(map_data, dict):
            for key in (
                "clearArea",
                "clearTime",
                "clearModule",
                "clearSign",
                "doTime",
                "transitCmd",
            ):
                if key in map_data:
                    attrs[key] = map_data[key]
            if map_data.get("map") is not None:
                attrs["map_raw_length"] = len(str(map_data.get("map")))
            if map_data.get("track") is not None:
                attrs["track_raw_length"] = len(str(map_data.get("track")))

        return attrs

    async def async_start(self) -> None:
        """Start cleaning."""
        await self._send_action("start")
        self._attr_activity = VacuumActivity.CLEANING
        self.async_write_ha_state()

    async def async_pause(self) -> None:
        """Pause cleaning."""
        await self._send_action("pause")
        self._attr_activity = VacuumActivity.PAUSED
        self.async_write_ha_state()

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop cleaning."""
        await self._send_action("pause")
        self._attr_activity = VacuumActivity.PAUSED
        self.async_write_ha_state()

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Return to dock."""
        await self._send_action("dock")
        self._attr_activity = VacuumActivity.RETURNING
        self.async_write_ha_state()

    async def async_clean_spot(self, **kwargs: Any) -> None:
        """Start spot cleaning."""
        await self._send_action("spot")
        await self._send_action("start")
        self._attr_activity = VacuumActivity.CLEANING
        self.async_write_ha_state()

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send custom command."""
        command = command.lower().strip()

        command_map = {
            "start": ["start"],
            "pause": ["pause"],
            "stop": ["pause"],
            "dock": ["dock"],
            "return_to_base": ["dock"],
            "auto": ["auto"],
            "auto_start": ["auto", "start"],
            "podel_zdi": ["podel_zdi"],
            "podel_zdi_start": ["podel_zdi", "start"],
            "edge": ["podel_zdi"],
            "edge_start": ["podel_zdi", "start"],
            "wall": ["podel_zdi"],
            "wall_start": ["podel_zdi", "start"],
            "spot": ["spot"],
            "spot_start": ["spot", "start"],
            "fan_off": ["fan_off"],
            "fan_normal": ["fan_normal"],
            "normal": ["fan_normal"],
            "fan_max": ["fan_max"],
            "max": ["fan_max"],
            "turbo": ["fan_max"],
            "fan_eco": ["fan_eco"],
            "eco": ["fan_eco"],
            "forward": ["forward"],
            "left": ["left"],
            "right": ["right"],
            "back": ["back"],
            "backward": ["back"],
            "manual_stop": ["manual_stop"],
            "stop_move": ["stop_move"],
            "map": ["map"],
            "get_map": ["map"],
            "keepalive": ["keepalive"],
        }

        if command not in command_map:
            raise HomeAssistantError(f"Unsupported Robzone command: {command}")

        for action in command_map[command]:
            await self._send_action(action)

        if command in ("dock", "return_to_base"):
            self._attr_activity = VacuumActivity.RETURNING
        elif command in ("pause", "stop", "manual_stop", "stop_move"):
            self._attr_activity = VacuumActivity.PAUSED
        elif command.endswith("_start") or command == "start":
            self._attr_activity = VacuumActivity.CLEANING

        self.async_write_ha_state()

    async def async_set_fan_speed(
        self, fan_speed: str, **kwargs: Any
    ) -> None:
        """Set suction power."""
        speed = str(fan_speed).lower().strip()
        action = FAN_SPEED_TO_ACTION.get(speed)
        if action is None:
            raise HomeAssistantError(
                f"Unsupported Robzone fan speed: {fan_speed}. "
                f"Use one of: {', '.join(self._attr_fan_speed_list)}"
            )

        await self._send_action(action)
        self._attr_fan_speed = "max" if speed == "turbo" else speed
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update entity state from coordinator/client cache."""
        self._apply_cached_status()

    async def _send_action(self, action: str) -> None:
        """Send command to Robzone client."""
        try:
            await self._client.async_send_command(action)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.exception("Robzone command failed: %s", action)
            raise HomeAssistantError(f"Robzone command failed: {action}") from exc

        self._apply_cached_status()

        if self._coordinator is not None:
            self._coordinator.async_set_updated_data(
                {
                    "status": dict(getattr(self._client, "last_status", {})),
                    "map": dict(getattr(self._client, "last_map", {})),
                }
            )

    def _apply_cached_status(self) -> None:
        """Apply last known cached status to the vacuum activity."""
        status = getattr(self._client, "last_status", {})
        if not isinstance(status, dict):
            return

        work_state = str(status.get("workState", status.get("work_state", "")))
        error = str(status.get("error", "0"))
        fan_value = str(status.get("fan", ""))
        if fan_value in FAN_VALUE_TO_SPEED:
            self._attr_fan_speed = FAN_VALUE_TO_SPEED[fan_value]

        if error not in ("", "0", "None", "none"):
            self._attr_activity = VacuumActivity.ERROR
        elif work_state == "1":
            self._attr_activity = VacuumActivity.CLEANING
        elif work_state == "2":
            self._attr_activity = VacuumActivity.DOCKED
        elif work_state == "4":
            self._attr_activity = VacuumActivity.RETURNING
        elif work_state == "5":
            self._attr_activity = VacuumActivity.IDLE
        elif work_state == "6":
            self._attr_activity = VacuumActivity.PAUSED
