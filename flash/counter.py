"""Counter implementation."""

from lib import logging
from lib.core import Sensor

_LOGGER = logging.getLogger(__name__)


class Counter(Sensor):
    """Representation of a Counter."""

    _type = int

    def __init__(
        self,
        sensor,
        point_lo_hi=7,
        point_hi_lo=0,
        *args,
        **kwargs,
    ):
        """Initialize the counter."""
        super().__init__(*args, **kwargs)
        self._sensor = sensor
        self._point_lo_hi = point_lo_hi
        self._point_hi_lo = point_hi_lo

        self._sensor_subscriber = self._sensor.subscribe(
            lambda x: self._sensor_changed(x)
        )

        self._sensor_changed(self._sensor.state)

    def __del__(self):
        """Cancel callbacks."""
        self._sensor.unsubscribe(self._sensor_subscriber)

    def _sensor_changed(self, new_state):
        """Handle sensor changes."""
        if new_state is None:
            return

        lastdigit = self.state % 10
        if self._point_hi_lo < self._point_lo_hi:
            state = lastdigit < self._point_hi_lo or self._point_lo_hi <= lastdigit
        else:
            state = self._point_lo_hi <= lastdigit and lastdigit < self._point_hi_lo

        if state == new_state:
            return

        new_lastdigit = self._point_lo_hi if new_state else self._point_hi_lo

        self.state += (
            new_lastdigit - lastdigit
            if new_lastdigit > lastdigit
            else new_lastdigit + 10 - lastdigit
        )
