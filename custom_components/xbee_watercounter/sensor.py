"""xbee_watercounter sensors."""

from __future__ import annotations

import datetime as dt

import voluptuous as vol
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfVolume
from homeassistant.core import callback
from homeassistant.helpers import entity_platform

from .const import DOMAIN
from .coordinator import XBeeWatercounterDataUpdateCoordinator
from .entity import XBeeWatercounterEntity

SERVICE_SET_VALUE = "set_value"

ATTR_VALUE = "value"
ATTR_RESET_CAUSE = "reset_cause"

BROWNOUT_RESET = "brownout"
LOCKUP_RESET = "lockup"
PWRON_RESET = "power on"
HARD_RESET = "hard reset"
WDT_RESET = "watchdog timer"
SOFT_RESET = "soft reset"
UNKNOWN_RESET = "unknown cause {}"
UNKNOWN = "unknown"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    sensors = []
    coordinator = hass.data[DOMAIN][entry.entry_id]

    for number in range(3):
        entity_description = SensorEntityDescription(
            key="xbee_watercounter_counter_" + str(number + 1),
            name="Counter",
            has_entity_name=True,
            icon="mdi:speedometer",
            device_class=SensorDeviceClass.WATER,
            native_unit_of_measurement=UnitOfVolume.LITERS,
            suggested_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
            suggested_display_precision=3,
            state_class=SensorStateClass.TOTAL,
        )
        sensors.append(
            XBeeWatercounterCounterSensor(
                name="counter",
                number=number,
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )

    entity_description = SensorEntityDescription(
        key="xbee_watercounter_uptime",
        name="Uptime",
        has_entity_name=True,
        translation_key="uptime",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    sensors.append(
        XBeeWatercounterUptimeSensor(
            name="uptime",
            coordinator=coordinator,
            entity_description=entity_description,
            conversion=lambda x: dt.datetime.fromtimestamp(x, tz=dt.timezone.utc)
            if x > 0
            else dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=x),
        )
    )

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_VALUE,
        {vol.Required(ATTR_VALUE): vol.Coerce(float)},
        f"async_{SERVICE_SET_VALUE}",
    )

    async_add_entities(sensors)


class XBeeWatercounterBaseSensor(XBeeWatercounterEntity, RestoreSensor):
    """Representation of an XBee Watercounter sensors."""

    def __init__(
        self,
        name,
        number,
        coordinator: XBeeWatercounterDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        conversion=None,
    ) -> None:
        """Initialize the switch class."""
        self.entity_description = entity_description
        self._attr_unique_id = coordinator.unique_id + (
            name if number is None else name + str(number)
        )
        super().__init__(coordinator, number)
        self._name = name
        self._number = number
        self._conversion = conversion

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        async def async_update_state(value):
            if self._conversion is not None:
                value = self._conversion(value)
            self._attr_native_value = value
            self.async_write_ha_state()

        subscriber_name = (
            self._name if self._number is None else self._name + "_" + str(self._number)
        )
        self.async_on_remove(
            self.coordinator.client.add_subscriber(subscriber_name, async_update_state)
        )


class XBeeWatercounterCounterSensor(XBeeWatercounterBaseSensor, RestoreSensor):
    """Representation of an XBee Watercounter Counter sensors."""

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        if self.coordinator.data.get("uptime", 0) > 0:
            self._handle_coordinator_update()
        else:
            if (old_data := await self.async_get_last_sensor_data()) is not None:
                if old_data.native_value is not None:
                    self._attr_native_value = old_data.native_value

            await self._update_device()

        self.async_on_remove(
            self.coordinator.add_subscriber("device_reset", self._update_device)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data.get("uptime", 0) <= 0:
            return  # Don't trust the data because the device has rebooted

        value = self.coordinator.data.get(self._name)
        if value is not None and self._number is not None:
            value = value.get(self._number)
        if self._conversion is not None:
            value = self._conversion(value)
        self._attr_native_value = value

        self.schedule_update_ha_state()

    async def _update_device(self):
        """Update device settings from HA on reset."""
        if self._attr_native_value is None:
            return
        if self._number is None:
            await self.coordinator.client.async_command(
                self._name, self._attr_native_value
            )
        else:
            await self.coordinator.client.async_command(
                self._name, self._number, self._attr_native_value
            )

    async def async_set_value(self, value: float) -> None:
        """Manually set value."""
        self._attr_native_value = int(value * 1000)
        await self._update_device()
        self.schedule_update_ha_state()


class XBeeWatercounterUptimeSensor(XBeeWatercounterBaseSensor):
    """Representation of an XBee Watercounter Uptime sensor."""

    def __init__(
        self,
        name,
        coordinator: XBeeWatercounterDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        conversion=None,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(name, None, coordinator, entity_description, conversion)
        self._attr_reset_cause = UNKNOWN

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self._handle_coordinator_update()

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        return {ATTR_RESET_CAUSE: self._attr_reset_cause}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        value = self.coordinator.data.get(self._name)
        if value <= 0:
            value = self.coordinator.data.get("new_" + self._name)

        self._attr_native_value = dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)

        reset_cause = self.coordinator.data.get("reset_cause")
        if reset_cause is not None:
            try:
                self._attr_reset_cause = {
                    3: HARD_RESET,
                    4: PWRON_RESET,
                    5: WDT_RESET,
                    6: SOFT_RESET,
                    9: LOCKUP_RESET,
                    11: BROWNOUT_RESET,
                }[reset_cause]
            except KeyError:
                self._attr_reset_cause = UNKNOWN_RESET.format(reset_cause)

        self.schedule_update_ha_state()
