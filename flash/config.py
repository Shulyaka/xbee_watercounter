"""Watercounter config."""

from gc import collect

from counter import Counter
from lib.xbeepin import DigitalInput, DigitalOutput
from machine import Pin
from valve import Valve

collect()

debug = False

Pin("D0", mode=Pin.ALT, alt=Pin.AF0_COMMISSION)
Pin("D5", mode=Pin.ALT, alt=Pin.AF5_ASSOC_IND)
Pin("D10", mode=Pin.ALT, alt=Pin.AF10_RSSI)
counter = [
    Counter(sensor=DigitalInput("D4")),
    Counter(sensor=DigitalInput("D6")),
    Counter(sensor=DigitalInput("D7")),
]
valve = [
    Valve(direction_switch=DigitalOutput("D1"), power_switch=DigitalOutput("D2")),
    Valve(direction_switch=DigitalOutput("D3"), power_switch=DigitalOutput("D8")),
    Valve(direction_switch=DigitalOutput("D9"), power_switch=DigitalOutput("D11")),
]

collect()
