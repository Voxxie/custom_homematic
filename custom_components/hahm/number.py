"""binary_sensor for HAHM."""
from __future__ import annotations

import logging
from typing import Any

from hahomematic.const import HmPlatform
from hahomematic.platforms.number import HmNumber

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ENTITY_CATEGORY_CONFIG
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .control_unit import ControlUnit
from .generic_entity import HaHomematicGenericEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HAHM number platform."""
    control_unit: ControlUnit = hass.data[DOMAIN][config_entry.entry_id]

    @callback
    def async_add_number(args: Any) -> None:
        """Add number from HAHM."""
        entities: list[HaHomematicGenericEntity] = []

        for hm_entity in args[0]:
            entities.append(HaHomematicNumber(control_unit, hm_entity))

        if entities:
            async_add_entities(entities)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            control_unit.async_signal_new_hm_entity(
                config_entry.entry_id, HmPlatform.NUMBER
            ),
            async_add_number,
        )
    )

    async_add_number(
        [control_unit.async_get_hm_entities_by_platform(HmPlatform.NUMBER)]
    )


class HaHomematicNumber(HaHomematicGenericEntity[HmNumber], NumberEntity):
    """Representation of the HomematicIP number entity."""

    _attr_entity_category = ENTITY_CATEGORY_CONFIG
    _attr_step = 0.1

    def __init__(
        self,
        control_unit: ControlUnit,
        hm_entity: HmNumber,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(control_unit=control_unit, hm_entity=hm_entity)
        self._attr_min_value = hm_entity.min
        self._attr_max_value = hm_entity.max
        self._attr_unit_of_measurement = hm_entity.unit

    @property
    def value(self) -> float | None:
        """Return the current value."""
        return self._hm_entity.state

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        await self._hm_entity.set_state(value)
