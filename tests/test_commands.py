"""Test commands."""

import logging
from json import loads as json_loads
from time import sleep as mock_sleep
from unittest.mock import patch

import commands
import pytest
from lib.core import Sensor, Switch
from lib.mainloop import main_loop
from machine import reset_cause as mock_reset_cause, soft_reset as mock_soft_reset
from valve import Valve
from xbee import atcmd as mock_atcmd, receive as mock_receive, transmit as mock_transmit


def test_commands():
    """Test Commands class."""

    assert mock_transmit.call_count == 0
    main_loop.run_once()
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "uptime": 0,
    }
    mock_transmit.reset_mock()

    counter = [Sensor() for x in range(3)]
    direction_switch = [Switch() for x in range(3)]
    power_switch = [Switch() for x in range(3)]
    valve = [
        Valve(direction_switch=direction_switch[x], power_switch=power_switch[x])
        for x in range(3)
    ]

    cmnds = commands.WatercounterCommands(
        counter=counter,
        valve=valve,
    )

    mock_receive.reset_mock()
    mock_receive.return_value = None
    cmnds.update()
    assert mock_receive.call_count == 1
    assert mock_transmit.call_count == 0

    mock_receive.reset_mock()
    mock_receive.return_value = {
        "broadcast": False,
        "dest_ep": 232,
        "sender_eui64": b"\x00\x13\xa2\x00A\xa0n`",
        "payload": "invalid_json",
        "sender_nwk": 0,
        "source_ep": 232,
        "profile": 49413,
        "cluster": 17,
    }

    with pytest.raises(ValueError) as excinfo:
        cmnds.update()

    assert mock_receive.call_count == 1
    assert mock_transmit.call_count == 0

    def command(cmd, args=None):
        mock_receive.reset_mock()
        mock_receive.return_value = {
            "broadcast": False,
            "dest_ep": 232,
            "sender_eui64": b"\x00\x13\xa2\x00A\xa0n`",
            "payload": '{"cmd": "' + cmd + '"}'
            if args is None
            else '{"cmd": "' + cmd + '", "args": ' + str(args) + "}",
            "sender_nwk": 0,
            "source_ep": 232,
            "profile": 49413,
            "cluster": 17,
        }
        cmnds.update()
        assert mock_receive.call_count == 2
        assert mock_transmit.call_count == 1
        assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
        resp = json_loads(mock_transmit.call_args[0][1])
        mock_transmit.reset_mock()
        value = resp[cmd + "_resp"]
        if isinstance(value, dict) and "err" in value:
            raise RuntimeError(value["err"])
        return value

    assert mock_transmit.call_count == 0
    main_loop.run_once()
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "uptime": 0,
    }
    mock_transmit.reset_mock()

    assert command("test") == "args: (), kwargs: {}"
    assert command("test", "true") == "args: (True,), kwargs: {}"
    assert command("test", '{"test": "123"}') == "args: (), kwargs: {'test': '123'}"
    assert command("test", "[1, 2, 3]") == "args: (1, 2, 3), kwargs: {}"
    assert (
        command("test", '[[1], {"test": "23"}]') == "args: (1,), kwargs: {'test': '23'}"
    )
    assert command("help") == [
        "atcmd",
        "bind",
        "close",
        "counter",
        "help",
        "logger",
        "open",
        "reset_cause",
        "soft_reset",
        "stop",
        "test",
        "unbind",
        "unique_id",
        "uptime",
        "valve",
    ]

    mock_atcmd.reset_mock()
    assert command("bind") == "OK"
    assert command("bind") == "OK"
    assert command("unique_id") == "0102030405060708"
    assert command("atcmd", '"VL"') == "OK"
    mock_atcmd.assert_called_once_with("VL")
    counter[0].state = 110
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"counter_0": 110}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    counter[0].state = 115
    assert mock_transmit.call_count == 0
    assert command("unbind") == "OK"

    assert (
        command("bind", '"\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"')
        == "OK"
    )
    valve[1].state = 60
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert mock_transmit.call_args[0][1] == '{"valve_1": 60}'
    mock_transmit.reset_mock()
    assert (
        command("unbind", '"\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"')
        == "OK"
    )
    valve[1].state = 70
    assert mock_transmit.call_count == 0

    assert command("bind") == "OK"
    valve[1].is_opening.state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"opening_1": true}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    valve[1].is_opening.state = False
    assert mock_transmit.call_count == 0

    assert command("bind") == "OK"
    valve[1].is_closing.state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "closing_1": True,
    }
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    valve[1].is_closing.state = False
    assert mock_transmit.call_count == 0

    assert command("valve", 1) == {
        "is_closing": False,
        "is_opening": False,
        "state": 70,
    }
    valve[1].state = 80
    assert command("valve", 1) == {
        "is_closing": False,
        "is_opening": False,
        "state": 80,
    }
    assert command("valve", [1, 90]) == "OK"
    assert valve[1].state == 90
    assert command("open", 0) == "OK"
    assert valve[0].is_opening.state is True
    assert command("close", 2) == "OK"
    assert valve[2].is_closing.state is True
    assert command("stop", 0) == "OK"
    assert valve[0].is_opening.state is False
    assert command("stop", 2) == "OK"
    assert valve[2].is_closing.state is False

    assert command("counter", [0, 120]) == "OK"
    assert counter[0].state == 120
    assert command("counter", 0) == 120

    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        assert command("logger", logging.WARNING) == "OK"
        assert logging.getLogger().getEffectiveLevel() == logging.WARNING
    else:
        assert command("logger", logging.DEBUG) == "OK"
        assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

    with patch("lib.core.logging.getLogger") as mock_getLogger:
        assert command("logger") == "OK"
        assert len(mock_getLogger.mock_calls) == 2
        assert mock_getLogger.mock_calls[0][1] == ()
        assert mock_getLogger.mock_calls[1][0] == "().setTarget"
        assert mock_getLogger.mock_calls[1][1] == (b"\x00\x13\xa2\x00A\xa0n`",)
        mock_getLogger.reset_mock()
        assert (
            command(
                "logger",
                '{"target": "\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"}',  # noqa: E501
            )
            == "OK"
        )
        assert len(mock_getLogger.mock_calls) == 2
        assert mock_getLogger.mock_calls[0][1] == ()
        assert mock_getLogger.mock_calls[1][0] == "().setTarget"
        assert mock_getLogger.mock_calls[1][1] == (b"\x00\x00\x00\x00\x00\x00\x00\x00",)

    assert command("uptime") == 0.0
    mock_sleep(5)
    assert command("uptime") == -5.0
    mock_sleep(3)
    assert command("uptime", 1700000000) == "OK"
    assert command("uptime") == 1700000000
    mock_sleep(2)
    assert command("uptime") == 1700000000

    with pytest.raises(RuntimeError) as excinfo:
        command("valve")
    assert "cmd_valve() missing 1 required positional argument: 'number'" in str(
        excinfo.value
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("uptime", '{"number": 2}')
    assert "cmd_uptime() got an unexpected keyword argument 'number'" in str(
        excinfo.value
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("counter", "[1, 2, 3]")
    assert (
        "cmd_counter() takes from 3 to 4 positional arguments but 5 were given"
        in str(excinfo.value)
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("do_magic")
    assert "No such command" in str(excinfo.value)

    mock_soft_reset.reset_mock()
    assert command("soft_reset") == "OK"
    main_loop.run_once()
    mock_soft_reset.assert_called_once_with()

    mock_reset_cause.reset_mock()
    assert command("reset_cause") == 6
    mock_reset_cause.assert_called_once_with()

    mock_transmit.side_effect = OSError("EAGAIN")

    with patch("lib.mainloop.main_loop.schedule_task") as mock_schedule_task:
        command("test")

    mock_schedule_task.assert_called_once()

    mock_transmit.side_effect = None
