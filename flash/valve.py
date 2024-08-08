"""Valve implementation."""

from lib import logging
from lib.core import Sensor, Switch
from lib.mainloop import main_loop

_LOGGER = logging.getLogger(__name__)


class Valve(Sensor):
    """Representation of a Valve device."""

    def __init__(
        self,
        direction_switch,
        power_switch,
        operation_time=15,
        discretization=5,
        *args,
        **kwargs,
    ):
        """Initialize the valve."""
        self._direction_switch = direction_switch
        self._power_switch = power_switch
        self._operation_time = operation_time
        self._discretization = discretization
        self.is_closing = Switch()
        self.is_opening = Switch()
        super().__init__(*args, **kwargs)

        self._operate_task = None

    def __del__(self):
        """Cancel callbacks."""
        self.stop()

    def _operate(self):
        """Update current status."""
        new_state = self.state
        if self.is_closing.state:
            if new_state is None:
                new_state = 100
            new_state -= self._discretization
            if new_state < 0:
                new_state = 0
            if new_state == 0:
                self.stop()
        elif self.is_opening.state:
            if new_state is None:
                new_state = 0
            new_state += self._discretization
            if new_state > 100:
                new_state = 100
            if new_state == 100:
                self.stop()
        else:
            _LOGGER.warning("Not in transition")
            self.stop()
            return
        self.state = new_state

    def stop(self):
        """Stop current operation."""
        main_loop.remove_task(self._operate_task)
        self._operate_task = None
        self._direction_switch.state = False
        self._power_switch.state = False
        self.is_opening.state = False
        self.is_closing.state = False

    def open(self):
        """Open the valve."""
        if self.is_opening.state:
            _LOGGER.info("Already opening")
            return
        if self.is_closing.state:
            self._operate()
            self.stop()
        self._direction_switch.state = True
        self._power_switch.state = True
        self.is_opening.state = True

        if self._operate_task:
            _LOGGER.warning("Task already scheduled")
            main_loop.remove_task(self._operate_task)
            self._operate_task = None

        self._operate_task = main_loop.schedule_task(
            lambda: self._operate(),
            period=self._operation_time * self._discretization * 10,
        )

    def close(self):
        """Close the valve."""
        if self.is_closing.state:
            _LOGGER.info("Already closing")
            return
        if self.is_opening.state:
            self._operate()
            self.stop()
        self._direction_switch.state = False
        self._power_switch.state = True
        self.is_closing.state = True

        if self._operate_task:
            _LOGGER.warning("Task already scheduled")
            main_loop.remove_task(self._operate_task)
            self._operate_task = None

        self._operate_task = main_loop.schedule_task(
            lambda: self._operate(),
            period=self._operation_time * self._discretization * 10,
        )
