"""Test xbee_watercounter."""

import datetime as dt
from unittest.mock import patch

import pytest
from homeassistant.const import UnitOfVolume
from homeassistant.core import State
from pytest_homeassistant_custom_component.common import (
    mock_restore_cache_with_extra_data,
)

from .conftest import commands
from .const import IEEE


def test_test(hass):
    """Workaround for https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/discussions/160."""


async def test_init_unknown(hass, caplog, data_from_device, test_config_entry):
    """Test component initialization with no device data."""

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


@pytest.fixture
def test_1():
    """Configure the data from the initialized device."""
    commands["uptime"].return_value = 1700000000
    commands["counter"]([0, 100])
    commands["counter"]([1, 200])
    commands["counter"]([2, 300])
    commands["counter"].reset_mock()


async def test_init_from_device(hass, data_from_device, test_1, test_config_entry):
    """Test component initialization from device data."""

    assert len(commands) == 10
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
    commands["uptime"].assert_called_once_with()
    commands["reset_cause"].assert_called_once_with()
    assert commands["valve"].call_count == 3
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["counter"].call_count == 3
    assert commands["counter"].call_args_list[0][0][0] == 0
    assert commands["counter"].call_args_list[1][0][0] == 1
    assert commands["counter"].call_args_list[2][0][0] == 2
    commands["open"].assert_not_called()
    commands["close"].assert_not_called()
    commands["stop"].assert_not_called()

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "0.1"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "0.2"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "0.3"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "open"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "open"


@pytest.fixture
def restore_state_1(hass):
    """Prepare restore state."""
    states = []

    restored_attributes = {
        "state_class": "total",
        "unit_of_measurement": "m³",
        "attribution": "Denis Shulyaka",
        "device_class": "water",
        "friendly_name": "Test",
    }

    fake_state = State(
        "sensor.xbee_watercounter_1_counter",
        "1.234",
        restored_attributes,
    )
    fake_extra_data = {
        "native_value": 1234,
        "native_unit_of_measurement": UnitOfVolume.LITERS,
    }

    states.append((fake_state, fake_extra_data))

    fake_state = State(
        "sensor.xbee_watercounter_2_counter",
        "2.345",
        restored_attributes,
    )
    fake_extra_data = {
        "native_value": 2345,
        "native_unit_of_measurement": UnitOfVolume.LITERS,
    }
    states.append((fake_state, fake_extra_data))

    fake_state = State(
        "sensor.xbee_watercounter_3_counter",
        "3.456",
        restored_attributes,
    )
    fake_extra_data = {
        "native_value": 3456,
        "native_unit_of_measurement": UnitOfVolume.LITERS,
    }

    states.append((fake_state, fake_extra_data))

    restored_attributes = {
        "current_position": 100,
        "attribution": "Denis Shulyaka",
        "device_class": "water",
        "friendly_name": "Test",
        "supported_features": 11,
    }

    fake_state = State(
        "valve.xbee_watercounter_1_valve",
        "open",
        restored_attributes,
    )
    states.append((fake_state, None))

    fake_state = State(
        "valve.xbee_watercounter_2_valve",
        "closed",
        restored_attributes,
    )
    states.append((fake_state, None))

    fake_state = State(
        "valve.xbee_watercounter_3_valve",
        "opening",
        restored_attributes,
    )
    states.append((fake_state, None))
    mock_restore_cache_with_extra_data(hass, states)


async def test_init_from_last_state(
    hass, data_from_device, restore_state_1, test_config_entry
):
    """Test component initialization from RestoreEntity last state."""

    assert len(commands) == 10
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
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
    commands["valve"].assert_not_called()
    # assert commands["valve"].call_count == 3
    # assert commands["valve"].call_args_list[0][0][0] == 0
    # assert commands["valve"].call_args_list[1][0][0] == 1
    # assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["counter"].call_count == 3
    assert commands["counter"].call_args_list[0][0][0] == [0, 1234]
    assert commands["counter"].call_args_list[1][0][0] == [1, 2345]
    assert commands["counter"].call_args_list[2][0][0] == [2, 3456]
    commands["open"].assert_not_called()
    commands["close"].assert_not_called()
    commands["stop"].assert_not_called()

    await hass.async_block_till_done()

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "2.345"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "3.456"
    # assert hass.states.get("valve.xbee_watercounter_1_valve").state == "open"
    # assert hass.states.get("valve.xbee_watercounter_2_valve").state == "closed"
    # assert hass.states.get("valve.xbee_watercounter_3_valve").state == "opening"
    assert hass.states.get("valve.xbee_watercounter_1_valve").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_2_valve").state == "unknown"
    assert hass.states.get("valve.xbee_watercounter_3_valve").state == "unknown"


async def test_init_from_history(hass, data_from_device, test_config_entry):
    """Test component initialization from recorder history."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["uptime"].return_value = -17
    commands["reset_cause"].reset_mock()
    commands["counter"].reset_mock()
    commands["unique_id"].reset_mock()
    commands["atcmd"].reset_mock()

    restored_attributes = {
        "state_class": "total",
        "unit_of_measurement": "m³",
        "attribution": "Denis Shulyaka",
        "device_class": "water",
        "friendly_name": "Test",
    }

    states = {
        "sensor.xbee_watercounter_1_counter": [
            State("sensor.xbee_watercounter_1_counter", "1.234", restored_attributes)
        ],
        "sensor.xbee_watercounter_2_counter": [
            State("sensor.xbee_watercounter_2_counter", "2.345", restored_attributes)
        ],
        "sensor.xbee_watercounter_3_counter": [
            State("sensor.xbee_watercounter_3_counter", "3.456", restored_attributes)
        ],
    }

    with patch(
        "homeassistant.components.recorder.history.get_last_state_changes",
        return_value=states,
    ) as mock_history:
        assert await hass.config_entries.async_reload(test_config_entry.entry_id)
        await hass.async_block_till_done()
        assert mock_history.call_count == 3

    assert len(commands) == 10
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
    commands["reset_cause"].assert_called_once_with()
    assert commands["uptime"].call_count == 2
    assert commands["uptime"].call_args_list[0][0] == ()
    assert (
        abs(
            commands["uptime"].call_args_list[1][0][0]
            + 17
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )
    commands["valve"].assert_not_called()
    # assert commands["valve"].call_count == 3
    # assert commands["valve"].call_args_list[0][0][0] == 0
    # assert commands["valve"].call_args_list[1][0][0] == 1
    # assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["counter"].call_count == 3
    assert commands["counter"].call_args_list[0][0][0] == [0, 1234]
    assert commands["counter"].call_args_list[1][0][0] == [1, 2345]
    assert commands["counter"].call_args_list[2][0][0] == [2, 3456]
    commands["open"].assert_not_called()
    commands["close"].assert_not_called()
    commands["stop"].assert_not_called()

    await hass.async_block_till_done()

    assert hass.states.get("sensor.xbee_watercounter_1_counter").state == "1.234"
    assert hass.states.get("sensor.xbee_watercounter_2_counter").state == "2.345"
    assert hass.states.get("sensor.xbee_watercounter_3_counter").state == "3.456"
    # assert hass.states.get("valve.xbee_watercounter_1_valve").state == "open"
    # assert hass.states.get("valve.xbee_watercounter_2_valve").state == "closed"
    # assert hass.states.get("valve.xbee_watercounter_3_valve").state == "opening"
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
