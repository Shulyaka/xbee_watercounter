"""Test device registry links and entity behavior after registration."""

import logging
from collections.abc import AsyncIterator, Callable, Iterator
from unittest.mock import MagicMock, call, patch

import pytest
from homeassistant.components.valve import SERVICE_OPEN_VALVE
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    label_registry as lr,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbee_watercounter.const import DOMAIN

from .conftest import commands
from .const import IEEE, MOCK_CONFIG

pytestmark = pytest.mark.usefixtures("data_from_device")


@pytest.fixture
def device_registrations(
    device_registry: dr.DeviceRegistry,
) -> Iterator[MagicMock]:
    """Capture metadata passed to the real device registry."""
    with patch.object(
        device_registry,
        "async_get_or_create",
        wraps=device_registry.async_get_or_create,
    ) as registrations:
        yield registrations


@pytest.fixture
async def unloaded_config_entry(hass: HomeAssistant) -> AsyncIterator[MockConfigEntry]:
    """Provide an entry whose setup is controlled by the migration test."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    yield entry
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()


async def test_device_topology(
    device_registrations: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    zha_device: dr.DeviceEntry,
    test_config_entry: MockConfigEntry,
) -> None:
    """The main unit links to ZHA and contains all three channel child devices."""
    assert device_registrations.called
    assert all(
        "via_device" not in call.kwargs for call in device_registrations.call_args_list
    )
    main_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, IEEE), test_config_entry.entry_id
    )
    assert main_device is not None
    assert main_device.via_device_id == zha_device.id

    device_ids = {main_device.id}
    for number in range(3):
        device = device_registry.async_get_child_device_by_identifier(
            (DOMAIN, f"{IEEE}-{number}"), test_config_entry.entry_id
        )
        assert device is not None
        assert device.parent_device_id == main_device.id
        device_ids.add(device.id)
        assert {
            entity.entity_id
            for entity in er.async_entries_for_device(entity_registry, device.id)
        } == {
            f"sensor.xbee_watercounter_{number + 1}_counter",
            f"valve.xbee_watercounter_{number + 1}_valve",
        }

    entities = er.async_entries_for_config_entry(
        entity_registry, test_config_entry.entry_id
    )
    assert {entity.device_id for entity in entities} == device_ids
    assert (
        len(
            dr.async_entries_for_config_entry(
                device_registry, test_config_entry.entry_id
            )
        )
        == 1
    )
    assert (
        len(
            dr.async_child_entries_for_config_entry(
                device_registry, test_config_entry.entry_id
            )
        )
        == 3
    )
    assert len(entities) == 7
    uptime = entity_registry.async_get("sensor.xbee_watercounter_main_unit_uptime")
    assert uptime is not None
    assert uptime.device_id == main_device.id


async def test_device_and_entity_ids_survive_reload(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    test_config_entry: MockConfigEntry,
) -> None:
    """Registration on reload preserves registry identities and user names."""
    counter = entity_registry.async_get("sensor.xbee_watercounter_1_counter")
    assert counter is not None
    entity_registry.async_update_entity(
        counter.entity_id, new_entity_id="sensor.kitchen_water"
    )
    device_registry.async_update_child_device(counter.device_id, name_by_user="Kitchen")

    main_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, IEEE), test_config_entry.entry_id
    )
    assert main_device is not None
    device_registry.async_update_device(
        main_device.id, name_by_user="Watercounter plant"
    )
    await hass.async_block_till_done()

    entities_before = {
        entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(
            entity_registry, test_config_entry.entry_id
        )
    }
    devices_before = {
        device.id: (
            device.identifiers,
            device.via_device_id,
            device.name_by_user,
            device.name,
            device.model,
            device.manufacturer,
            device.hw_version,
            device.sw_version,
        )
        for device in dr.async_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    }

    children_before = {
        device.id: (
            device.identifiers,
            device.parent_device_id,
            device.name_by_user,
            device.name,
            device.area_id,
            device.labels,
        )
        for device in dr.async_child_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    }

    assert await hass.config_entries.async_reload(test_config_entry.entry_id)
    await hass.async_block_till_done()

    assert {
        entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(
            entity_registry, test_config_entry.entry_id
        )
    } == entities_before
    assert {
        device.id: (
            device.identifiers,
            device.via_device_id,
            device.name_by_user,
            device.name,
            device.model,
            device.manufacturer,
            device.hw_version,
            device.sw_version,
        )
        for device in dr.async_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    } == devices_before
    assert {
        device.id: (
            device.identifiers,
            device.parent_device_id,
            device.name_by_user,
            device.name,
            device.area_id,
            device.labels,
        )
        for device in dr.async_child_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    } == children_before
    assert hass.states.get("sensor.kitchen_water") is not None
    assert hass.states.get("sensor.xbee_watercounter_1_counter") is None


async def test_existing_channels_become_child_devices(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    label_registry: lr.LabelRegistry,
    zha_device: dr.DeviceEntry,
    unloaded_config_entry: MockConfigEntry,
) -> None:
    """Adopt existing channels without changing registry identities or user settings."""

    def legacy_channel_info(
        *, identifiers: set[tuple[str, str]], name: str, parent_device_id: str
    ) -> dr.DeviceInfo:
        return dr.DeviceInfo(
            identifiers=identifiers,
            name=name,
            via_device_id=parent_device_id,
            model="XBee3",
            manufacturer="Digi",
            hw_version="4247",
            sw_version="1014",
        )

    entry = unloaded_config_entry
    with patch(
        "custom_components.xbee_watercounter.entity.ChildDeviceInfo",
        side_effect=legacy_channel_info,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    main_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, IEEE), entry.entry_id
    )
    assert main_device is not None
    assert main_device.via_device_id == zha_device.id
    assert not dr.async_child_entries_for_config_entry(device_registry, entry.entry_id)
    label = label_registry.async_create("Water supply")
    old_channels = {}
    for number in range(3):
        device = device_registry.async_get_device_by_identifier(
            (DOMAIN, f"{IEEE}-{number}"), entry.entry_id
        )
        assert device is not None
        area = area_registry.async_create(f"Channel {number + 1}")
        old_channels[number] = device_registry.async_update_device(
            device.id,
            name_by_user=f"Water counter {number + 1}",
            area_id=area.id,
            labels={label.label_id},
        )
        entity_registry.async_update_entity(
            f"sensor.xbee_watercounter_{number + 1}_counter",
            new_entity_id=f"sensor.water_{number + 1}",
        )
    await hass.async_block_till_done()
    entities_before = {
        entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    }

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    main_after = device_registry.async_get_device_by_identifier(
        (DOMAIN, IEEE), entry.entry_id
    )
    assert main_after is not None
    assert main_after.id == main_device.id
    assert main_after.via_device_id == zha_device.id
    assert len(dr.async_entries_for_config_entry(device_registry, entry.entry_id)) == 1
    assert (
        len(dr.async_child_entries_for_config_entry(device_registry, entry.entry_id))
        == 3
    )
    for number, previous_device in old_channels.items():
        child = device_registry.async_get_child_device_by_identifier(
            (DOMAIN, f"{IEEE}-{number}"), entry.entry_id
        )
        assert child is not None
        assert child.id == previous_device.id
        assert child.parent_device_id == main_device.id
        assert child.identifiers == previous_device.identifiers
        assert child.name == previous_device.name
        assert child.name_by_user == previous_device.name_by_user
        assert child.area_id == previous_device.area_id
        assert child.labels == previous_device.labels
        assert hass.states.get(f"sensor.water_{number + 1}") is not None
    assert {
        entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    } == entities_before


async def test_missing_zha_device_retries(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    zha_device: dr.DeviceEntry,
    unloaded_config_entry: MockConfigEntry,
) -> None:
    """Missing ZHA ownership delays setup until the physical device is registered."""
    device_registry.async_remove_device(zha_device.id)
    unrelated_entry = MockConfigEntry(domain="other", entry_id="other")
    unrelated_entry.add_to_hass(hass)
    unrelated_device = device_registry.async_get_or_create(
        config_entry_id=unrelated_entry.entry_id, identifiers={("zha", IEEE)}
    )
    entry = unloaded_config_entry
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert "XBee device is not registered with ZHA" in entry.reason
    assert (
        device_registry.async_get_device_by_identifier((DOMAIN, IEEE), entry.entry_id)
        is None
    )

    physical_device = device_registry.async_get_or_create(
        config_entry_id="test_zha", identifiers={("zha", IEEE)}, name="XBee"
    )
    assert physical_device.id != unrelated_device.id
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    main_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, IEEE), entry.entry_id
    )
    assert main_device is not None
    assert main_device.via_device_id == physical_device.id


@pytest.mark.usefixtures("test_config_entry")
async def test_all_channels_after_reload(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    data_from_device: Callable[[HomeAssistant, str, dict[str, object]], None],
) -> None:
    """All child devices receive counter updates and send their channel commands."""
    assert await hass.config_entries.async_reload("test")
    await hass.async_block_till_done()

    data_from_device(
        hass,
        IEEE,
        {
            "counter_0": 12345,
            "counter_1": 23456,
            "counter_2": 34567,
            "valve_0": 0,
            "valve_1": 0,
            "valve_2": 0,
        },
    )
    await hass.async_block_till_done()

    for number, value in enumerate(("12.345", "23.456", "34.567")):
        counter = hass.states.get(f"sensor.xbee_watercounter_{number + 1}_counter")
        assert counter is not None
        assert counter.state == value
        valve = hass.states.get(f"valve.xbee_watercounter_{number + 1}_valve")
        assert valve is not None
        assert valve.state == "closed"

    commands["open"].reset_mock()
    await hass.services.async_call(
        "valve",
        SERVICE_OPEN_VALVE,
        {
            ATTR_ENTITY_ID: [
                f"valve.xbee_watercounter_{number + 1}_valve" for number in range(3)
            ]
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert commands["open"].call_count == 3
    commands["open"].assert_has_calls([call(0), call(1), call(2)], any_order=True)
    for number in range(3):
        assert (
            hass.states.get(f"valve.xbee_watercounter_{number + 1}_valve").state
            == "opening"
        )

    commands["counter"].reset_mock()
    for number, value in enumerate((13, 24, 35)):
        entity_id = f"sensor.xbee_watercounter_{number + 1}_counter"
        await hass.services.async_call(
            DOMAIN,
            "set_value",
            {ATTR_ENTITY_ID: entity_id, "value": value},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert float(hass.states.get(entity_id).state) == value
    assert commands["counter"].call_args_list == [
        call([0, 13000]),
        call([1, 24000]),
        call([2, 35000]),
    ]
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]
