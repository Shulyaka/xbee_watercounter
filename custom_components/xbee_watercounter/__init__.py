"""The xbee_watercounter custom component."""

from homeassistant.components.zha import DOMAIN as ZHA_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, NAME
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
    hass.data[DOMAIN][entry.entry_id] = coordinator = (
        XBeeWatercounterDataUpdateCoordinator(hass=hass, client=client)
    )

    entry.async_on_unload(lambda: coordinator.stop())

    await coordinator.async_config_entry_first_refresh()

    device_registry = dr.async_get(hass)
    for zha_entry in hass.config_entries.async_entries(ZHA_DOMAIN):
        if (
            zha_device := device_registry.async_get_device_by_identifier(
                (ZHA_DOMAIN, client.device_ieee), zha_entry.entry_id
            )
        ) is not None:
            break
    else:
        raise ConfigEntryNotReady("XBee device is not registered with ZHA")

    coordinator.zha_device_id = zha_device.id
    coordinator.device_id = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, client.device_ieee)},
        name=NAME + " Main Unit",
        via_device_id=zha_device.id,
    ).id

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
