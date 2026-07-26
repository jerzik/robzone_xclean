"""Sensor platform for Robzone Duoro Xclean LAN."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfArea, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass(frozen=True)
class SensorDescription:
    """Robzone sensor description."""

    key: str
    name: str
    icon: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    unit: str | None = None
    entity_category: EntityCategory | None = None
    enabled_default: bool = True
    value_fn: Callable[[dict[str, Any], dict[str, Any]], Any] | None = None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _work_state(status: dict[str, Any], _map: dict[str, Any]) -> str | None:
    value = status.get("workState")
    names = {
        "1": "uklízí",
        "2": "návrat do docku",
        "5": "start / rozjezd",
        "6": "pauza / standby",
    }
    return names.get(str(value), str(value)) if value is not None else None


def _work_mode(status: dict[str, Any], _map: dict[str, Any]) -> str | None:
    value = status.get("workMode")
    names = {
        "0": "auto",
        "1": "spot",
        "4": "podél zdi",
        "6": "auto",
    }
    return names.get(str(value), str(value)) if value is not None else None


def _error(status: dict[str, Any], _map: dict[str, Any]) -> str | None:
    value = status.get("error")
    if value is None:
        return None
    return "bez chyby" if str(value) == "0" else f"chyba {value}"


def _map_value(key: str) -> Callable[[dict[str, Any], dict[str, Any]], Any]:
    return lambda _status, map_data: map_data.get(key)


def _map_int_value(key: str) -> Callable[[dict[str, Any], dict[str, Any]], int | None]:
    return lambda _status, map_data: _int_or_none(map_data.get(key))


SENSORS: tuple[SensorDescription, ...] = (
    SensorDescription(
        key="battery",
        name="Baterie",
        icon="mdi:battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        unit=PERCENTAGE,
        value_fn=lambda status, _map: _int_or_none(status.get("battery")),
    ),
    SensorDescription(
        key="work_state",
        name="Stav práce",
        icon="mdi:robot-vacuum",
        value_fn=_work_state,
    ),
    SensorDescription(
        key="work_mode",
        name="Režim úklidu",
        icon="mdi:format-list-bulleted",
        value_fn=_work_mode,
    ),
    SensorDescription(
        key="fan",
        name="Výkon ventilátoru",
        icon="mdi:fan",
        value_fn=lambda status, _map: status.get("fan"),
    ),
    SensorDescription(
        key="error",
        name="Chyba",
        icon="mdi:alert-circle-outline",
        value_fn=_error,
    ),
    SensorDescription(
        key="clear_area",
        name="Uklizená plocha",
        icon="mdi:floor-plan",
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfArea.SQUARE_METERS,
        value_fn=_map_int_value("clearArea"),
    ),
    SensorDescription(
        key="clear_time",
        name="Čas úklidu z mapy",
        icon="mdi:timer-outline",
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfTime.SECONDS,
        value_fn=_map_int_value("clearTime"),
    ),
    SensorDescription(
        key="clear_sign",
        name="ID aktuálního úklidu",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_map_value("clearSign"),
    ),
    SensorDescription(
        key="map_raw",
        name="Mapa RAW Base64",
        icon="mdi:map-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_default=False,
        value_fn=_map_value("map"),
    ),
    SensorDescription(
        key="track_raw",
        name="Trasa RAW Base64",
        icon="mdi:map-marker-path",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_default=False,
        value_fn=_map_value("track"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Robzone sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]

    async_add_entities(
        [RobzoneSensor(entry, client, coordinator, description) for description in SENSORS],
        True,
    )


class RobzoneSensor(CoordinatorEntity, SensorEntity):
    """Robzone sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        client: Any,
        coordinator: Any,
        description: SensorDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._client = client
        self._description = description

        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_native_unit_of_measurement = description.unit
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_default

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title or "Robzone Duoro Xclean 5",
            "manufacturer": "Robzone / HCTRobot compatible",
            "model": "Duoro Xclean 5",
            "configuration_url": f"http://{entry.data.get('host', '')}",
        }

    @property
    def native_value(self) -> Any:
        """Return native sensor value."""
        status = getattr(self._client, "last_status", {})
        map_data = getattr(self._client, "last_map", {})

        if not isinstance(status, dict):
            status = {}
        if not isinstance(map_data, dict):
            map_data = {}

        if self._description.value_fn is None:
            return None

        return self._description.value_fn(status, map_data)
