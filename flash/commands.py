"""Module defines remote commands."""

from json import dumps as json_dumps

from lib.core import Commands


class WatercounterCommands(Commands):
    """Define application remote commands."""

    def __init__(
        self,
        counter,
        valve,
    ):
        """Init the module."""
        super().__init__()
        self._counter = counter
        self._valve = valve

        self._binds = {
            "counter": [{}, {}, {}],
            "valve": [{}, {}, {}],
            "opening": [{}, {}, {}],
            "closing": [{}, {}, {}],
        }

    def __del__(self):
        """Cancel callbacks."""
        super().__del__()
        self.cmd_unbind()

    def cmd_valve(self, sender_eui64, number, state=None):
        """Get or set the current valve state."""
        if state is None:
            return {
                "state": self._valve[number].state,
                "is_opening": self._valve[number].is_opening.state,
                "is_closing": self._valve[number].is_closing.state,
            }
        self._valve[number].state = state
        return "OK"

    def cmd_open(self, sender_eui64, number):
        """Open the valve."""
        self._valve[number].open()
        return "OK"

    def cmd_close(self, sender_eui64, number):
        """Close the valve."""
        self._valve[number].close()
        return "OK"

    def cmd_stop(self, sender_eui64, number):
        """Cancel current operation."""
        self._valve[number].stop()
        return "OK"

    def cmd_counter(self, sender_eui64, number, state=None):
        """Get or set the counter state."""
        if state is None:
            return self._counter[number].state
        self._counter[number].state = state
        return "OK"

    def cmd_bind(self, sender_eui64, target=None):
        """Subscribe to updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        def bind(entity, binds, name):
            if target not in binds:
                binds[target] = entity.subscribe(
                    lambda x: self._transmit(target, json_dumps({name: x}))
                )

        for number in range(3):
            bind(
                self._counter[number],
                self._binds["counter"][number],
                "counter_{}".format(number),
            )
            bind(
                self._valve[number],
                self._binds["valve"][number],
                "valve_{}".format(number),
            )
            bind(
                self._valve[number].is_opening,
                self._binds["opening"][number],
                "opening_{}".format(number),
            )
            bind(
                self._valve[number].is_closing,
                self._binds["closing"][number],
                "closing_{}".format(number),
            )
        return "OK"

    def cmd_unbind(self, sender_eui64=None, target=None):
        """Unsubscribe to updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        def unbind(entity, binds):
            if target is None:
                for bind in binds.values():
                    entity.unsubscribe(bind)
                binds.clear()
            elif target in binds:
                entity.unsubscribe(binds.pop(target))

        for number in range(3):
            unbind(self._counter[number], self._binds["counter"][number])
            unbind(self._valve[number], self._binds["valve"][number])
            unbind(self._valve[number].is_opening, self._binds["opening"][number])
            unbind(self._valve[number].is_closing, self._binds["closing"][number])
        return "OK"
