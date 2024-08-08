"""The xbee_watercounter custom component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import (
    XBeeWatercounterApiClient,
    XBeeWatercounterDataUpdateCoordinator,
)

CONF_DEVICE_IEEE = "device_ieee"

PLATFORMS: list[Platform] = [
    Platform.VALVE,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    client = XBeeWatercounterApiClient(
        hass=hass, device_ieee=entry.data[CONF_DEVICE_IEEE]
    )
    hass.data[DOMAIN][
        entry.entry_id
    ] = coordinator = XBeeWatercounterDataUpdateCoordinator(hass=hass, client=client)

    entry.async_on_unload(lambda: coordinator.stop())

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
