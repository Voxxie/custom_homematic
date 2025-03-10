"""Generic entity for the HomematicIP Cloud component."""
from __future__ import annotations

import logging
from typing import Any, Generic

from hahomematic.const import HM_VIRTUAL_REMOTES, IDENTIFIERS_SEPARATOR
from hahomematic.entity import CallbackEntity
from hahomematic.helpers import get_device_address
from hahomematic.hub import BaseHubEntity, HmSystemVariable

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN
from .control_unit import ControlUnit
from .entity_helpers import get_entity_description
from .helpers import HmGenericEntity

_LOGGER = logging.getLogger(__name__)


class HaHomematicGenericEntity(Generic[HmGenericEntity], Entity):
    """Representation of the HomematicIP generic entity."""

    _attr_should_poll = False

    def __init__(
        self,
        control_unit: ControlUnit,
        hm_entity: HmGenericEntity,
    ) -> None:
        """Initialize the generic entity."""
        self._cu: ControlUnit = control_unit
        self._hm_entity: HmGenericEntity = hm_entity
        if entity_description := get_entity_description(self._hm_entity):
            self.entity_description = entity_description
        # Marker showing that the Hm device hase been removed.
        self._hm_device_removed = False

        self._attr_name = hm_entity.name
        self._attr_unique_id = hm_entity.unique_id

        _LOGGER.debug("Setting up %s", self.name)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._hm_entity.available

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device specific attributes."""
        info = self._hm_entity.device_info

        if isinstance(self._hm_entity, HmSystemVariable):
            identifiers = info["identifiers"]
        else:
            address = get_device_address(self._hm_entity.address)
            if address in HM_VIRTUAL_REMOTES:
                address = f"{self._cu.central.instance_name}_{address}"
            identifiers = {
                (DOMAIN, address),
                (
                    DOMAIN,
                    f"{get_device_address(self._hm_entity.address)}{IDENTIFIERS_SEPARATOR}{self._hm_entity.client.interface_id}",
                ),
            }

        return DeviceInfo(
            identifiers=identifiers,
            manufacturer=info["manufacturer"],
            model=info["model"],
            name=info["name"],
            sw_version=info["sw_version"],
            # Link to the homematic control unit.
            via_device=info.get("via_device"),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the generic entity."""
        return self._hm_entity.extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Register callbacks and load initial data."""
        if isinstance(self._hm_entity, (BaseHubEntity, CallbackEntity)):
            self._hm_entity.register_update_callback(self._async_device_changed)
            self._hm_entity.register_remove_callback(self._async_device_removed)
        self._cu.async_add_hm_entity(hm_entity=self._hm_entity)
        # Init data of entity.
        if hasattr(self._hm_entity, "load_data"):
            await self._hm_entity.load_data()

    @callback
    def _async_device_changed(self, *args: Any, **kwargs: Any) -> None:
        """Handle device state changes."""
        # Don't update disabled entities
        if self.enabled:
            _LOGGER.debug("Event %s", self.name)
            self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device Changed Event for %s not fired. Entity is disabled",
                self.name,
            )

    async def async_will_remove_from_hass(self) -> None:
        """Run when hmip device will be removed from hass."""

        # Only go further if the device/entity should be removed from registries
        # due to a removal of the HM device.

        if self._hm_device_removed:
            try:
                self._cu.async_remove_hm_entity(self._hm_entity)
                self._async_remove_from_registries()
            except KeyError as err:
                _LOGGER.debug("Error removing HM device from registry: %s", err)

    @callback
    def _async_remove_from_registries(self) -> None:
        """Remove entity/device from registry."""

        # Remove callback from device.
        self._hm_entity.unregister_update_callback(self._async_device_changed)
        self._hm_entity.unregister_remove_callback(self._async_device_removed)

        if not self.registry_entry:
            return

        if device_id := self.registry_entry.device_id:
            # Remove from device registry.
            device_registry = dr.async_get(self.hass)
            if device_id in device_registry.devices:
                # This will also remove associated entities from entity registry.
                device_registry.async_remove_device(device_id)
        else:
            # Remove from entity registry.
            # Only relevant for entities that do not belong to a device.
            if entity_id := self.registry_entry.entity_id:
                entity_registry = er.async_get(self.hass)
                if entity_id in entity_registry.entities:
                    entity_registry.async_remove(entity_id)

    @callback
    def _async_device_removed(self, *args: Any, **kwargs: Any) -> None:
        """Handle hm device removal."""
        # Set marker showing that the Hm device hase been removed.
        self._hm_device_removed = True
        self.hass.async_create_task(self.async_remove(force_remove=True))
