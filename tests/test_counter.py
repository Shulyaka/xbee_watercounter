"""The tests for the Counter class."""


import pytest
from counter import Counter
from lib.core import Sensor, Switch


def test_counter_lo_hi():
    """Test counter class with low point below high point."""

    sensor = Switch()
    counter = Counter(sensor, point_lo_hi=7, point_hi_lo=2)

    assert isinstance(counter, Sensor)

    assert sensor.state is False
    assert counter.state == 2

    sensor.state = True
    assert counter.state == 7

    sensor.state = False
    assert counter.state == 12

    counter.state = 1
    assert counter.state == 1

    counter.state = 5
    assert counter.state == 5


def test_counter_hi_lo():
    """Test counter class with low point above high point."""

    sensor = Switch()
    counter = Counter(sensor, point_lo_hi=2, point_hi_lo=7)

    assert isinstance(counter, Sensor)

    assert sensor.state is False
    assert counter.state == 0

    sensor.state = True
    assert counter.state == 2

    sensor.state = False
    assert counter.state == 7

    counter.state = 1
    assert counter.state == 1

    counter.state = 5
    assert counter.state == 5


@pytest.mark.parametrize(
    "initial, sensor_update, target",
    (
        (0, True, 0),
        (1, True, 1),
        (2, True, 7),
        (100003, True, 100007),
        (7, True, 7),
        (8, True, 8),
        (10, True, 10),
        (0, False, 2),
        (99991, False, 99992),
        (2, False, 2),
        (3, False, 3),
        (7, False, 12),
    ),
)
def test_counter_transition_lo_hi(initial, sensor_update, target):
    """Test counter increment."""

    sensor = Switch()
    counter = Counter(sensor, point_lo_hi=7, point_hi_lo=2)

    sensor.state = not sensor_update
    counter.state = initial

    sensor.state = sensor_update
    assert counter.state == target


@pytest.mark.parametrize(
    "initial, sensor_update, target",
    (
        (0, False, 0),
        (1, False, 1),
        (2, False, 7),
        (100003, False, 100007),
        (7, False, 7),
        (8, False, 8),
        (10, False, 10),
        (0, True, 2),
        (99991, True, 99992),
        (2, True, 2),
        (3, True, 3),
        (7, True, 12),
    ),
)
def test_counter_transition_hi_lo(initial, sensor_update, target):
    """Test counter increment."""

    sensor = Switch()
    counter = Counter(sensor, point_lo_hi=2, point_hi_lo=7)

    sensor.state = not sensor_update
    counter.state = initial

    sensor.state = sensor_update
    assert counter.state == target
