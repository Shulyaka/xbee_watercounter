"""Test xbee_watercounter sensors."""

import datetime as dt

from homeassistant.const import ATTR_ENTITY_ID

from .conftest import commands
from .const import IEEE

ENTITY = "sensor.xbee_watercounter_main_unit_uptime"


def test_test(hass):
    """Workaround for https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/discussions/160."""


async def test_counter(hass, data_from_device, test_config_entry):
    """Test counter sensor."""

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "unknown"
    data_from_device(hass, IEEE, {"counter_0": 12345})
    await hass.async_block_till_done()

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "12.345"

    await hass.services.async_call(
        "xbee_watercounter",
        "set_value",
        {ATTR_ENTITY_ID: "sensor.xbee_watercounter_1_counter", "value": 12.346},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "12.346"


async def test_uptime_set(hass, data_from_device, test_config_entry):
    """Test absolute uptime set if relative uptime is returned from the device."""

    commands["uptime"].reset_mock()
    commands["uptime"].return_value = -30

    data_from_device(hass, IEEE, {"uptime": -30})
    await hass.async_block_till_done()

    assert commands["uptime"].call_count == 1
    assert (
        abs(
            commands["uptime"].call_args_list[0][0][0]
            + 30
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )

    assert (
        (
            hass.states.get(ENTITY).state
            == (dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=-29))
            .replace(microsecond=0)
            .isoformat()
        )
        or (
            hass.states.get(ENTITY).state
            == (dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=-30))
            .replace(microsecond=0)
            .isoformat()
        )
        or (
            hass.states.get(ENTITY).state
            == (dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=-31))
            .replace(microsecond=0)
            .isoformat()
        )
    )


async def test_reset_cause(hass, data_from_device, test_config_entry):
    """Test reset cause attribute."""
    assert hass.states.get(ENTITY).attributes.get("reset_cause") == "soft reset"

    commands["reset_cause"].return_value = 7

    data_from_device(hass, IEEE, {"uptime": 0})
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY).attributes.get("reset_cause") == "unknown cause 7"
