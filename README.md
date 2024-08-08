# xbee_watercounter
![CI](https://github.com/Shulyaka/xbee_watercounter/actions/workflows/xbee_watercounter.yml/badge.svg?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/Shulyaka/xbee_watercounter/badge.svg?branch=master)](https://coveralls.io/github/Shulyaka/xbee_watercounter?branch=master)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

MicroPython firmware and Home Assistant custom component for my DIY water meter an electric valve

## About
I have water meters on my pipes with a couple of electric wires each. The wires close and open the electric flow as they count. Also I have electric valves that can open or close those pipes.
I've added some relay switches and an XBee to connect it to Home Assistant.

This repository has two parts:

1. MicroPython firmware to run on XBee itself
2. HomeAssistant custom component

### You may find parts of this repo useful for your own MicroPython projects, such as:
1. Main loop implementation with task scheduling. Be careful with the stack size, which is very small on XBees, if you experience unexplained software reboots, then refactor your code scheduling tasks into the main loop instead of calling them directly because that would use the stack
2. Hardware abstraction layer for different kinds of inputs/outputs (virtual, gpio, external relay boards, binary or analog) with low pass filter and trigger callbacks support
3. JSON command interface with the host over ZigBee
4. A remote logger
5. An example of Github-CI pipeline with tests for both micropython and HA custom component
