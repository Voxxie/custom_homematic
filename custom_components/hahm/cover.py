"""binary_sensor for HAHM."""
from __future__ import annotations

from abc import ABC
import logging
from typing import Any

from hahomematic.const import HmPlatform
from hahomematic.devices.cover import HmBlind, HmCover, HmGarage

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up the HAHM cover platform."""
    control_unit: ControlUnit = hass.data[DOMAIN][config_entry.entry_id]

    @callback
    def async_add_cover(args: Any) -> None:
        """Add cover from HAHM."""
        entities: list[HaHomematicGenericEntity] = []

        for hm_entity in args[0]:
            if isinstance(hm_entity, HmBlind):
                entities.append(HaHomematicBlind(control_unit, hm_entity))
            elif isinstance(hm_entity, HmCover):
                entities.append(HaHomematicCover(control_unit, hm_entity))
            elif isinstance(hm_entity, HmGarage):
                entities.append(HaHomematicGarage(control_unit, hm_entity))

        if entities:
            async_add_entities(entities)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            control_unit.async_signal_new_hm_entity(
                config_entry.entry_id, HmPlatform.COVER
            ),
            async_add_cover,
        )
    )

    async_add_cover([control_unit.async_get_hm_entities_by_platform(HmPlatform.COVER)])


class HaHomematicCover(HaHomematicGenericEntity[HmCover], CoverEntity):
    """Representation of the HomematicIP cover entity."""

    @property
    def current_cover_position(self) -> int | None:
        """
        Return current position of cover.
        """
        return self._hm_entity.current_cover_position

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        # Hm cover is closed:1 -> open:0
        if ATTR_POSITION in kwargs:
            position = float(kwargs[ATTR_POSITION])
            await self._hm_entity.set_cover_position(position)

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        return self._hm_entity.is_closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._hm_entity.open_cover()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._hm_entity.close_cover()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the device if in motion."""
        await self._hm_entity.stop_cover()


class HaHomematicBlind(HaHomematicGenericEntity[HmBlind], CoverEntity, ABC):
    """Representation of the HomematicIP blind entity."""

    @property
    def current_cover_position(self) -> int | None:
        """
        Return current position of cover.
        """
        return self._hm_entity.current_cover_position

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        # Hm cover is closed:1 -> open:0
        if ATTR_POSITION in kwargs:
            position = float(kwargs[ATTR_POSITION])
            await self._hm_entity.set_cover_position(position)

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        return self._hm_entity.is_closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._hm_entity.open_cover()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._hm_entity.close_cover()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the device if in motion."""
        await self._hm_entity.stop_cover()

    @property
    def current_cover_tilt_position(self) -> int | None:
        """
        Return current tilt position of cover.
        """
        return self._hm_entity.current_cover_tilt_position

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific tilt position."""
        if ATTR_TILT_POSITION in kwargs:
            position = float(kwargs[ATTR_TILT_POSITION])
            await self._hm_entity.set_cover_tilt_position(position)

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the tilt."""
        await self._hm_entity.open_cover_tilt()

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the tilt."""
        await self._hm_entity.close_cover_tilt()

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the device if in motion."""
        await self._hm_entity.stop_cover_tilt()


class HaHomematicGarage(HaHomematicGenericEntity[HmGarage], CoverEntity):
    """Representation of the HomematicIP garage entity."""

    @property
    def current_cover_position(self) -> int | None:
        """
        Return current position of cover.
        """
        return self._hm_entity.current_cover_position

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        # Hm cover is closed:1 -> open:0
        if ATTR_POSITION in kwargs:
            position = float(kwargs[ATTR_POSITION])
            await self._hm_entity.set_cover_position(position)

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        return self._hm_entity.is_closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._hm_entity.open_cover()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._hm_entity.close_cover()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the device if in motion."""
        await self._hm_entity.stop_cover()
