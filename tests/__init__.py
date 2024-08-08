"""Tests for xbee_watercounter."""

import sys

sys.path = ["tests/modules", "flash"] + sys.path
sys.modules["time"] = __import__("mock_time")
sys.modules["gc"] = __import__("mock_gc")
