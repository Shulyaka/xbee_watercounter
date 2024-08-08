"""Test xbee_watercounter valves."""

import pytest
from homeassistant.components.valve import (
    DOMAIN as VALVE,
    SERVICE_CLOSE_VALVE,
    SERVICE_OPEN_VALVE,
    SERVICE_STOP_VALVE,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN

from .conftest import commands
from .const import IEEE

ENT_VALVE1 = "valve.xbee_watercounter_1_valve"
ENT_VALVE2 = "valve.xbee_watercounter_2_valve"
ENT_VALVE3 = "valve.xbee_watercounter_3_valve"


def test_valve_init(hass, data_from_device, test_config_entry):
    """Test that all valve entities are created."""

    assert hass.states.get(ENT_VALVE1).state == STATE_UNKNOWN
    assert hass.states.get(ENT_VALVE2).state == STATE_UNKNOWN
    assert hass.states.get(ENT_VALVE3).state == STATE_UNKNOWN


@pytest.mark.parametrize(
    "entity, number",
    (
        (ENT_VALVE1, 0),
        (ENT_VALVE2, 1),
        (ENT_VALVE3, 2),
    ),
)
async def test_valve_services(
    hass, data_from_device, test_config_entry, entity, number
):
    """Test valve open/close."""

    assert hass.states.get(entity).state == STATE_UNKNOWN

    await hass.services.async_call(
        VALVE,
        SERVICE_OPEN_VALVE,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )

    assert hass.states.get(entity).state == STATE_OPENING
    commands["open"].assert_called_once_with(number)

    await hass.services.async_call(
        VALVE,
        SERVICE_CLOSE_VALVE,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )

    assert hass.states.get(entity).state == STATE_CLOSING
    commands["close"].assert_called_once_with(number)

    await hass.services.async_call(
        VALVE,
        SERVICE_STOP_VALVE,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )

    assert hass.states.get(entity).state == STATE_UNKNOWN
    commands["stop"].assert_called_once_with(number)


@pytest.mark.parametrize(
    "entity, number",
    (
        (ENT_VALVE1, 0),
        (ENT_VALVE2, 1),
        (ENT_VALVE3, 2),
    ),
)
async def test_valve_remote_update(
    hass, data_from_device, test_config_entry, entity, number
):
    """Test valve remote open/close."""

    assert hass.states.get(entity).state == STATE_UNKNOWN

    data_from_device(hass, IEEE, {f"valve_{number}": 100})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_OPEN

    data_from_device(hass, IEEE, {f"valve_{number}": 0})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_CLOSED

    data_from_device(hass, IEEE, {f"opening_{number}": True})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_OPENING

    data_from_device(hass, IEEE, {f"opening_{number}": False})
    data_from_device(hass, IEEE, {f"closing_{number}": True})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_CLOSING
