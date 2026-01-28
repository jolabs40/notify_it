import logging
import json
import time
import asyncio
import websockets
from homeassistant.components.notify import NotifyEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration de la plateforme de notification."""
    async_add_entities([NotifyItEntity(entry)])

class NotifyItEntity(NotifyEntity):
    """Représentation de l'entité de notification Notify-it."""

    def __init__(self, entry):
        self._host = entry.data["host"]
        self._device_id = entry.data.get("device_id", "ha_default")
        self._attr_name = entry.title
        self._attr_unique_id = self._device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Jolabs40",
            model="Android TV Box",
        )

    async def async_send_message(self, message="", title=None, data=None, **kwargs):
        """Envoi du message vers la TV via WebSocket."""
        uri = f"ws://{self._host}:{DEFAULT_PORT}"
        final_payload = None
        
        _LOGGER.info(f"Notify-it : Tentative d'envoi vers {self._host}")

        # Détection du mode (JSON Expert ou Texte Simple)
        try:
            if "{" in message:
                start_index = message.find("{")
                json_str = message[start_index:]
                parsed_json = json.loads(json_str)
                if isinstance(parsed_json, dict) and "elements" in parsed_json:
                    final_payload = parsed_json
        except Exception:
            pass

        if not final_payload:
            # Mode Simple : On crée un bandeau par défaut
            final_payload = {
                "duration": 10000,
                "elements": [{
                    "type": "text",
                    "content": message,
                    "style": {
                        "left": 5, "top": 80, "width": 90, "height": 15,
                        "size": 25, "color": "#FFFFFF", "bgColor": "#000000CC", "radius": 15
                    }
                }]
            }

        try:
            async with websockets.connect(uri, open_timeout=5) as ws:
                # 1. Authentification
                auth = {
                    "type": "AUTH",
                    "deviceId": self._device_id,
                    "deviceName": "Home Assistant",
                    "timestamp": int(time.time() * 1000),
                    "signature": "signed_by_ha"
                }
                await ws.send(json.dumps(auth))
                await asyncio.sleep(0.2)
                
                # 2. Envoi du design
                await ws.send(json.dumps(final_payload))
                _LOGGER.info("Notify-it : Message envoyé avec succès")
        except Exception as e:
            _LOGGER.error(f"Erreur de connexion Notify-it : {e}")