"""xbee_watercounter valves."""

from __future__ import annotations

from homeassistant.components.valve import (
    ValveDeviceClass,
    ValveEntity,
    ValveEntityDescription,
    ValveEntityFeature,
)
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import XBeeWatercounterDataUpdateCoordinator
from .entity import XBeeWatercounterEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    valves = []
    coordinator = hass.data[DOMAIN][entry.entry_id]
    for number in range(3):
        entity_description = ValveEntityDescription(
            key="xbee_watercounter_valve_" + str(number + 1),
            name="Valve",
            has_entity_name=True,
            device_class=ValveDeviceClass.WATER,
            reports_position=True,
        )
        valves.append(
            XBeeWatercounterValve(
                name="valve",
                number=number,
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )

    async_add_entities(valves)


class XBeeWatercounterValve(XBeeWatercounterEntity, ValveEntity):
    """Representation of an XBee Watercounter valves."""

    _attr_supported_features = (
        ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE | ValveEntityFeature.STOP
    )

    def __init__(
        self,
        name,
        number,
        coordinator: XBeeWatercounterDataUpdateCoordinator,
        entity_description: ValveEntityDescription,
    ) -> None:
        """Initialize the valve class."""
        self.entity_description = entity_description
        self._attr_unique_id = coordinator.unique_id + (
            name if number is None else name + str(number)
        )
        super().__init__(coordinator, number)
        self._name = name
        self._number = number

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self._handle_coordinator_update()

        async def async_update_state(value):
            self._attr_current_valve_position = value
            self.async_write_ha_state()

        subscriber_name = self._name + "_" + str(self._number)
        self.async_on_remove(
            self.coordinator.client.add_subscriber(subscriber_name, async_update_state)
        )

        async def async_update_opening(value):
            self._attr_is_opening = value
            self.async_write_ha_state()

        subscriber_name = "opening_" + str(self._number)
        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                subscriber_name, async_update_opening
            )
        )

        async def async_update_closing(value):
            self._attr_is_closing = value
            self.async_write_ha_state()

        subscriber_name = "closing_" + str(self._number)
        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                subscriber_name, async_update_closing
            )
        )

        self.async_on_remove(
            self.coordinator.add_subscriber("device_reset", self._update_device)
        )

    async def async_open_valve(self) -> None:
        """Open valve."""
        resp = await self.coordinator.client.async_command("open", self._number)

        if resp == "OK":
            self._attr_is_opening = True
            self._attr_is_closing = False
            self.async_write_ha_state()

    async def async_close_valve(self) -> None:
        """Close the valve."""
        resp = await self.coordinator.client.async_command("close", self._number)

        if resp == "OK":
            self._attr_is_opening = False
            self._attr_is_closing = True
            self.async_write_ha_state()

    async def async_stop_valve(self) -> None:
        """Stop the valve."""
        resp = await self.coordinator.client.async_command("stop", self._number)

        if resp == "OK":
            self._attr_is_opening = False
            self._attr_is_closing = False
            self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data.get(self._name, {}).get(self._number)
        if data is None:
            return

        self._attr_current_valve_position = data["state"]
        self._attr_is_opening = data["is_opening"]
        self._attr_is_closing = data["is_closing"]

        self.schedule_update_ha_state()

    async def _update_device(self):
        """Update device settings from HA on reset."""
        await self.coordinator.client.async_command(
            "valve", self._number, self._attr_current_valve_position
        )
