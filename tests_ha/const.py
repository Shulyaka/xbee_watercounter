"""Constants for xbee_watercounter tests."""

from custom_components.xbee_watercounter import CONF_DEVICE_IEEE

IEEE = "00:11:22:33:44:55:66:77"

# Mock config data to be used across multiple tests
MOCK_CONFIG = {
    CONF_DEVICE_IEEE: IEEE,
}
