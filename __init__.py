"""Robzone Duoro Xclean custom integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AUTH_CODE,
    CONF_TARGET_ID,
    DEFAULT_SCAN_INTERVAL_SECONDS,
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
        """Poll live map/status data from the vacuum."""
        try:
            await client.async_get_map()
        except Exception as exc:  # noqa: BLE001
            # Do not make the whole integration unavailable because map polling
            # can fail while the vacuum sleeps or is rebooting.
            raise UpdateFailed(str(exc)) from exc

        return {
            "status": dict(client.last_status),
            "map": dict(client.last_map),
        }

    coordinator: DataUpdateCoordinator[dict[str, Any]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Robzone Duoro Xclean LAN",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Do not block setup if the vacuum is sleeping/unreachable at HA start.
    try:
        await coordinator.async_refresh()
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Initial Robzone refresh failed: %s", exc)

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
