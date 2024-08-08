"""Test xbee_watercounter config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow

from custom_components.xbee_watercounter.const import DOMAIN

from .const import MOCK_CONFIG


@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.xbee_watercounter.async_setup_entry",
        return_value=True,
    ):
        yield


def test_test(hass):
    """Workaround for https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/discussions/160."""


async def test_successful_config_flow(hass, data_from_device):
    """Test a successful config flow."""
    # Init first step
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "00:11:22:33:44:55:66:77"
    assert result["data"] == MOCK_CONFIG
    assert result["options"] == {}
    assert result["result"]


@patch("custom_components.xbee_watercounter.coordinator.XBeeWatercounterApiClient._cmd")
async def test_failed_config_flow(cmd_mock, hass):
    """Test a failed config flow due to timeout error."""
    cmd_mock.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "No response to unique_id command"}
