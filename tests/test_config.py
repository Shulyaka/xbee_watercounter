"""Test config."""

import config
from lib.core import Sensor
from valve import Valve


def test_config():
    """Test config."""
    assert isinstance(config.debug, bool)
    assert isinstance(config.counter, list)
    assert len(config.counter) == 3
    assert isinstance(config.valve, list)
    assert len(config.valve) == 3
    for x in range(3):
        assert isinstance(config.counter[x], Sensor)
        assert isinstance(config.valve[x], Valve)
