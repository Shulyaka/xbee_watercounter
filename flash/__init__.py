"""Main module of the watercounter."""

from gc import collect, mem_alloc, mem_free

import config
from commands import WatercounterCommands
from lib import logging
from lib.mainloop import main_loop
from micropython import kbd_intr

collect()

_LOGGER = logging.getLogger(__name__)

WatercounterCommands(
    config.counter,
    config.valve,
)
collect()

main_loop.schedule_task(lambda: _LOGGER.debug("Main loop started"))

if config.debug:
    print("Debug mode enabled")

    x = 0
    for counter in config.counter:
        counter.subscribe((lambda n: lambda v: print("counter{} = {}".format(n, v)))(x))
        x += 1

    x = 0
    for valve in config.valve:
        valve.subscribe((lambda n: lambda v: print("valve{} = {}".format(n, v)))(x))
        valve.is_opening.subscribe(
            (lambda n: lambda v: print("valve{}.is_opening = {}".format(n, v)))(x)
        )
        valve.is_closing.subscribe(
            (lambda n: lambda v: print("valve{}.is_closing = {}".format(n, v)))(x)
        )
        x += 1

    def _stats():
        """Print mem stats."""
        alloc = mem_alloc()
        print("MEM {:.2%}".format(alloc / (alloc + mem_free())))

    main_loop.schedule_task(_stats, period=1000)

else:
    from machine import WDT

    main_loop.schedule_task(
        (lambda wdt: lambda: wdt.feed())(WDT(timeout=30000)), period=1000
    )
    kbd_intr(-1)

collect()
