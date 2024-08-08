"""Global fixtures for xbee_watercounter integration."""

import json
from functools import partial
from unittest.mock import DEFAULT, MagicMock, patch

import pytest
from homeassistant.core import callback
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbee_watercounter.const import DOMAIN

from .const import MOCK_CONFIG

pytest_plugins = "pytest_homeassistant_custom_component.plugins"


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss
# persistent notifications. These calls would fail without this fixture since the
# persistent_notification integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This is used to access calls and configure command responses
calls = []
cached_values = {}


_NO_ARGS = "no args"


def _cmd_handler(cmd, args=_NO_ARGS):
    number = None
    if isinstance(args, list):
        if args and isinstance(args[0], int):
            number = args[0]
            args = args[1:]
        if len(args) == 1:
            args = args[0]
        elif not args:
            args = _NO_ARGS
    elif isinstance(args, dict):
        if "number" in args:
            number = args.pop("number")
        if len(args) == 1:
            args = args.values()[0]
        elif not args:
            args = _NO_ARGS
    elif isinstance(args, int) and cmd in (
        "valve",
        "open",
        "close",
        "stop",
        "counter",
    ):
        number = args
        args = _NO_ARGS

    if args == _NO_ARGS:
        if number is not None and cmd in cached_values and number in cached_values[cmd]:
            return cached_values[cmd][number]
        return DEFAULT

    if number is not None:
        cached_values.setdefault(cmd, {})[number] = args
    else:
        commands[cmd].return_value = args
    return "OK"


commands = {
    "valve": MagicMock(side_effect=partial(_cmd_handler, "valve")),
    "open": MagicMock(side_effect=partial(_cmd_handler, "open")),
    "close": MagicMock(side_effect=partial(_cmd_handler, "close")),
    "stop": MagicMock(side_effect=partial(_cmd_handler, "stop")),
    "counter": MagicMock(side_effect=partial(_cmd_handler, "counter")),
    "atcmd": MagicMock(),
    "uptime": MagicMock(side_effect=partial(_cmd_handler, "uptime")),
    "reset_cause": MagicMock(),
}


# This fixture enables two-way communication with the device. The calls are logged
# in the calls array. The command responses can be configured with command dict.
@pytest.fixture(name="data_from_device")
def data_from_device_fixture(hass):
    """Configure fake two-way communication."""
    for x in commands.values():
        x.reset_mock()

    cached_values.clear()

    commands["atcmd"].return_value = (
        "XBee3-PRO Zigbee 3.0 TH RELE: 1010\rBuild: Aug  2 2022 14:33:22\r"
        "HV: 4247\rBootloader: 1B2 Compiler: 8030001\rStack: 6760\rOK\x00"
    )
    commands["valve"].return_value = {
        "state": 100,
        "is_opening": False,
        "is_closing": False,
    }
    commands["open"].return_value = "OK"
    commands["close"].return_value = "OK"
    commands["stop"].return_value = "OK"
    commands["counter"].return_value = 1234
    commands["uptime"].return_value = -10
    commands["reset_cause"].return_value = 6

    def data_from_device(hass, ieee, data):
        """Simulate receiving data from device."""
        hass.bus.async_fire(
            "zha_event",
            {
                "device_ieee": ieee,
                "unique_id": ieee + ":232:0x0008",
                "device_id": "abcdef01234567899876543210fedcba",
                "endpoint_id": 232,
                "cluster_id": 8,
                "command": "receive_data",
                "args": {"data": json.dumps(data)},
            },
        )

    @callback
    def log_call(call):
        """Log service calls."""
        calls.append(call)
        data = json.loads(call.data["params"]["data"])
        cmd = data["cmd"]
        if cmd not in commands:
            commands[cmd] = MagicMock(return_value="OK")
        if "args" in data:
            response = commands[cmd](data["args"])
        else:
            response = commands[cmd]()
        data_from_device(hass, call.data["ieee"], {cmd + "_resp": response})

    hass.services.async_register("zha", "issue_zigbee_cluster_command", log_call)

    calls.clear()

    yield data_from_device

    hass.services.async_remove("zha", "issue_zigbee_cluster_command")


# This fixture loads and unloads the test config entry
@pytest.fixture
async def test_config_entry(hass):
    """Load and unload hass config entry."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")

    await hass.config_entries.async_add(config_entry)
    await hass.async_block_till_done()

    yield config_entry

    await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
