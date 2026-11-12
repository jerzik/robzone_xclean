"""Robzone Duoro Xclean custom integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_AUTH_CODE,
    CONF_TARGET_ID,
    DOMAIN,
)
from .robzone_client import RobzoneClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["vacuum", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Robzone Duoro Xclean from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    client = RobzoneClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        auth_code=entry.data[CONF_AUTH_CODE],
        target_id=entry.data[CONF_TARGET_ID],
    )

    async def _async_update_data() -> dict[str, Any]:
        """Return cached command responses without sending a TCP request."""
        return {
            "status": dict(client.last_status),
            "map": dict(client.last_map),
        }

    coordinator: DataUpdateCoordinator[dict[str, Any]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Robzone Duoro Xclean LAN",
        update_method=_async_update_data,
    )

    # The vacuum firmware reacts unreliably to unsolicited map requests.
    # Keep entities alive from the local cache and update it only after an
    # explicit control command. No background TCP connection is opened here.
    coordinator.async_set_updated_data(
        {
            "status": dict(client.last_status),
            "map": dict(client.last_map),
        }
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Home Assistant 2026+ warns when platform modules are imported inside the
    # event loop. Preload the platform modules in the executor and only then
    # forward setup to HA.
    for platform in PLATFORMS:
        await hass.async_add_executor_job(
            __import__, f"custom_components.{DOMAIN}.{platform}"
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Robzone Duoro Xclean config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok
