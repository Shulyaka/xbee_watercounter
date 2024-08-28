"""Watercounter config."""

from gc import collect

from counter import Counter
from lib.xbeepin import DigitalInput, DigitalOutput
from machine import Pin
from valve import Valve

collect()

debug = False

Pin("D0", mode=Pin.ALT, alt=Pin.AF0_COMMISSION)
aux_led = DigitalOutput("D4")
aux_button = DigitalInput("D5")
Pin("D10", mode=Pin.ALT, alt=Pin.AF10_RSSI)
counter = [
    Counter(sensor=DigitalInput("D2")),
    Counter(sensor=DigitalInput("D3")),
    Counter(sensor=DigitalInput("D9")),
]
valve = [
    Valve(direction_switch=DigitalOutput("D12"), power_switch=DigitalOutput("D15")),
    Valve(direction_switch=DigitalOutput("D16"), power_switch=DigitalOutput("D17")),
    Valve(direction_switch=DigitalOutput("D18"), power_switch=DigitalOutput("D19")),
]

collect()
