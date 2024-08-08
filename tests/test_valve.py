"""The tests for the Valve class."""

from time import sleep as mock_sleep
from unittest.mock import MagicMock

import pytest
from lib.core import Sensor, Switch
from lib.mainloop import main_loop
from valve import Valve


@pytest.fixture
def setup_valve():
    """Initialize components."""
    direction_switch = Switch()
    power_switch = Switch()
    valve = Valve(
        direction_switch=direction_switch,
        power_switch=power_switch,
        operation_time=4,
        discretization=25,
    )
    return direction_switch, power_switch, valve


def test_valve(setup_valve):
    """Test Valve class."""

    direction_switch, power_switch, valve = setup_valve

    assert isinstance(valve, Sensor)

    assert direction_switch.state is False
    assert power_switch.state is False
    assert valve.is_opening.state is False
    assert valve.is_closing.state is False
    assert valve.state is None


def test_valve_open(setup_valve):
    """Test Valve open."""

    direction_switch, power_switch, valve = setup_valve

    callback = MagicMock()
    valve.subscribe(callback)

    valve.open()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state is None
    callback.assert_not_called()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state == 25
    callback.assert_called_once_with(25)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state == 50
    callback.assert_called_once_with(50)

    callback.reset_mock()

    # Open again while opening
    valve.open()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state == 75
    callback.assert_called_once_with(75)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is False
    assert valve.is_opening.state is False
    assert valve.is_closing.state is False
    assert valve.state == 100
    callback.assert_called_once_with(100)


def test_valve_close(setup_valve):
    """Test Valve close."""

    direction_switch, power_switch, valve = setup_valve

    callback = MagicMock()
    valve.subscribe(callback)

    valve.close()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state is None
    callback.assert_not_called()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state == 75
    callback.assert_called_once_with(75)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state == 50
    callback.assert_called_once_with(50)

    callback.reset_mock()

    # Close again while closing
    valve.close()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state == 25
    callback.assert_called_once_with(25)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is False
    assert valve.is_opening.state is False
    assert valve.is_closing.state is False
    assert valve.state == 0
    callback.assert_called_once_with(0)


def test_valve_close_open(setup_valve):
    """Test Valve open while closing."""

    direction_switch, power_switch, valve = setup_valve

    callback = MagicMock()
    valve.subscribe(callback)

    valve.close()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state is None
    callback.assert_not_called()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state == 75
    callback.assert_called_once_with(75)

    callback.reset_mock()
    valve.open()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state == 50
    callback.assert_called_once_with(50)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state == 75
    callback.assert_called_once_with(75)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is False
    assert valve.is_opening.state is False
    assert valve.is_closing.state is False
    assert valve.state == 100
    callback.assert_called_once_with(100)


def test_valve_open_close(setup_valve):
    """Test Valve close while opening."""

    direction_switch, power_switch, valve = setup_valve

    callback = MagicMock()
    valve.subscribe(callback)

    valve.open()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state is None
    callback.assert_not_called()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state == 25
    callback.assert_called_once_with(25)

    callback.reset_mock()
    valve.close()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state == 50
    callback.assert_called_once_with(50)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state == 25
    callback.assert_called_once_with(25)

    callback.reset_mock()
    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is False
    assert valve.is_opening.state is False
    assert valve.is_closing.state is False
    assert valve.state == 0
    callback.assert_called_once_with(0)


def test_valve_open_stop(setup_valve):
    """Test Valve stop while opening."""

    direction_switch, power_switch, valve = setup_valve

    callback = MagicMock()
    valve.subscribe(callback)

    valve.open()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state is None
    callback.assert_not_called()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is True
    assert power_switch.state is True
    assert valve.is_opening.state is True
    assert valve.is_closing.state is False
    assert valve.state == 25
    callback.assert_called_once_with(25)

    callback.reset_mock()

    valve.stop()

    assert direction_switch.state is False
    assert power_switch.state is False
    assert valve.is_opening.state is False
    assert valve.is_closing.state is False
    assert valve.state == 25
    callback.assert_not_called()


def test_valve_close_stop(setup_valve):
    """Test Valve stop while closing."""

    direction_switch, power_switch, valve = setup_valve

    callback = MagicMock()
    valve.subscribe(callback)

    valve.close()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state is None
    callback.assert_not_called()

    mock_sleep(1)
    main_loop.run_once()

    assert direction_switch.state is False
    assert power_switch.state is True
    assert valve.is_opening.state is False
    assert valve.is_closing.state is True
    assert valve.state == 75
    callback.assert_called_once_with(75)

    callback.reset_mock()

    valve.stop()

    assert direction_switch.state is False
    assert power_switch.state is False
    assert valve.is_opening.state is False
    assert valve.is_closing.state is False
    assert valve.state == 75
    callback.assert_not_called()
