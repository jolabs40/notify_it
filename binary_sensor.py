import logging
import asyncio
import websockets
from datetime import timedelta
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

# Vérification toutes les 30 secondes
SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    name = entry.title
    # On crée le capteur
    async_add_entities([NotifyItStatus(host, name, entry.entry_id)], True)

class NotifyItStatus(BinarySensorEntity):
    """Capteur qui indique si la TV est connectée."""

    def __init__(self, host, name, entry_id):
        self._host = host
        self._attr_name = f"{name} Status"
        self._attr_unique_id = f"{entry_id}_status"
        # Device Class 'connectivity' gère automatiquement les icônes (Ethernet/Wifi)
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._is_connected = False
        
        # Infos pour lier ce capteur au même appareil que la notification
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="Jolabs40",
            model="Android TV Box",
            sw_version="1.0.2",
        )

    @property
    def is_on(self):
        """Retourne True si connecté, False sinon."""
        return self._is_connected

    @property
    def icon(self):
        """Icône dynamique : Vert (check) ou Rouge (alert)."""
        return "mdi:television-ambient-light" if self._is_connected else "mdi:television-off"

    async def async_update(self):
        """Test de connexion WebSocket rapide (Ping)."""
        uri = f"ws://{self._host}:{DEFAULT_PORT}"
        try:
            # On tente d'ouvrir le socket et de le refermer aussitôt
            async with websockets.connect(uri, open_timeout=3):
                self._is_connected = True
        except Exception:
            self._is_connected = False