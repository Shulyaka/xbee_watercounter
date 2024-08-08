"""Test xbee_watercounter."""

import datetime as dt

from .conftest import commands
from .const import IEEE


def test_test(hass):
    """Workaround for https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/discussions/160."""


async def test_init(hass, caplog, data_from_device, test_config_entry):
    """Test component initialization."""

    assert len(commands) == 10
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
    commands["valve"].assert_not_called()
    commands["open"].assert_not_called()
    commands["close"].assert_not_called()
    commands["stop"].assert_not_called()
    commands["counter"].assert_not_called()
    commands["reset_cause"].assert_called_once_with()
    assert commands["uptime"].call_count == 2
    assert commands["uptime"].call_args_list[0][0] == ()
    assert (
        abs(
            commands["uptime"].call_args_list[1][0][0]
            + 10
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )

    data_from_device(hass, IEEE, {"log": {"msg": "Test log", "sev": 20}})
    await hass.async_block_till_done()
    assert "Test log" in caplog.text

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "unknown"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "unknown"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "unknown"


async def test_refresh(hass, data_from_device, test_config_entry):
    """Test reinitialize on device reset."""

    data_from_device(hass, IEEE, {"counter_0": 1234})
    data_from_device(hass, IEEE, {"valve_1": 95})
    data_from_device(hass, IEEE, {"valve_2": 0})
    await hass.async_block_till_done()

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["uptime"].return_value = 0
    commands["reset_cause"].reset_mock()
    commands["counter"].reset_mock()

    data_from_device(hass, IEEE, {"uptime": 0})
    await hass.async_block_till_done()
    commands["bind"].assert_called_once_with()
    assert commands["valve"].call_count == 3
    assert commands["valve"].call_args_list[0][0][0] == [0, None]
    assert commands["valve"].call_args_list[1][0][0] == [1, 95]
    assert commands["valve"].call_args_list[2][0][0] == [2, 0]
    commands["open"].assert_not_called()
    commands["close"].assert_not_called()
    commands["stop"].assert_not_called()
    commands["counter"].assert_called_once_with([0, 1234])
    commands["reset_cause"].assert_called_once_with()
    assert commands["uptime"].call_count == 1
    assert (
        abs(
            commands["uptime"].call_args_list[0][0][0]
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 1.5
    )

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "unknown"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "closed"


async def test_reload(hass, data_from_device, test_config_entry):
    """Test config entry reload."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["counter"].reset_mock()
    commands["counter"].return_value = 1234

    assert await hass.config_entries.async_reload(test_config_entry.entry_id)
    await hass.async_block_till_done()

    commands["bind"].assert_called_once_with()
    commands["uptime"].assert_called_once_with()
    assert commands["valve"].call_count == 3
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["counter"].call_count == 3
    assert commands["counter"].call_args_list[0][0][0] == 0
    assert commands["counter"].call_args_list[1][0][0] == 1
    assert commands["counter"].call_args_list[2][0][0] == 2

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "1.234"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "open"


async def test_coordinator_update(hass, data_from_device, test_config_entry):
    """Test coordinator data update."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["counter"].reset_mock()

    coordinator = hass.data["xbee_watercounter"][test_config_entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert commands["valve"].call_count == 3
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["counter"].call_count == 3
    assert commands["counter"].call_args_list[0][0][0] == 0
    assert commands["counter"].call_args_list[1][0][0] == 1
    assert commands["counter"].call_args_list[2][0][0] == 2

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "1.234"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "open"


async def test_device_reset(hass, data_from_device, test_config_entry):
    """Test device reset identified during coordinator data update."""

    data_from_device(hass, IEEE, {"counter_0": 1234})
    data_from_device(hass, IEEE, {"valve_1": 95})
    data_from_device(hass, IEEE, {"valve_2": 0})
    await hass.async_block_till_done()

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["uptime"].return_value = -12
    commands["reset_cause"].reset_mock()
    commands["counter"].reset_mock()

    coordinator = hass.data["xbee_watercounter"][test_config_entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    commands["bind"].assert_called_once_with()
    assert commands["uptime"].call_count == 2
    assert commands["uptime"].call_args_list[0][0] == ()
    assert (
        abs(
            commands["uptime"].call_args_list[1][0][0]
            + 12
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )

    assert commands["valve"].call_count == 3
    assert commands["valve"].call_args_list[0][0][0] == [0, None]
    assert commands["valve"].call_args_list[1][0][0] == [1, 95]
    assert commands["valve"].call_args_list[2][0][0] == [2, 0]
    commands["open"].assert_not_called()
    commands["close"].assert_not_called()
    commands["stop"].assert_not_called()
    commands["counter"].assert_called_once_with([0, 1234])
    commands["reset_cause"].assert_called_once_with()

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "unknown"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "closed"


async def test_connection_recovery(hass, data_from_device, test_config_entry):
    """Test device coming back online after being unavailable during last update."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["counter"].reset_mock()

    coordinator = hass.data["xbee_watercounter"][test_config_entry.entry_id]
    coordinator.last_update_success = False
    data_from_device(hass, IEEE, {"counter_0": 1234})
    await hass.async_block_till_done()

    commands["bind"].assert_called_once_with()
    commands["uptime"].assert_called_once_with()
    assert commands["valve"].call_count == 3
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["counter"].call_count == 3
    assert commands["counter"].call_args_list[0][0][0] == 0
    assert commands["counter"].call_args_list[1][0][0] == 1
    assert commands["counter"].call_args_list[2][0][0] == 2

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "1.234"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "open"
