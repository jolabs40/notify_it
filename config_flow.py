import asyncio
import json
import uuid
import time
import logging
import websockets
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

class NotifyItConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            _LOGGER.warning(f"Tentative de connexion Notify-it sur : {user_input['host']}")
            
            result = await self.async_pair_device(user_input["host"])
            if result:
                return result
            
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host", default="192.168.2.128"): str
            }),
            errors=errors
        )

    async def async_pair_device(self, host):
        device_id = str(uuid.uuid4())
        uri = f"ws://{host}:{DEFAULT_PORT}"
        
        try:
            async with websockets.connect(uri, open_timeout=5) as websocket:
                # 1. Demande d'AUTH
                auth_payload = {
                    "type": "AUTH",
                    "deviceId": device_id,
                    "deviceName": "Home Assistant",
                    "timestamp": int(time.time() * 1000),
                    "signature": "pairing"
                }
                await websocket.send(json.dumps(auth_payload, separators=(',', ':')))
                
                # 2. Attente du clic utilisateur
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                
                if data.get("status") == "paired":
                    
                    # --- DÉBUT SÉQUENCE DE SUCCÈS ---
                    # On envoie un message visuel direct sur la TV
                    success_msg = {
                        "elements": [
                            {
                                "type": "text",
                                "content": "HOME ASSISTANT CONNECTÉ !",
                                "style": {
                                    "left": 10, "top": 40, 
                                    "width": 80, "height": 15,
                                    "size": 35, "weight": "bold",
                                    "color": "#FFFFFF", 
                                    "bgColor": "#2E7D32", # Vert fonce
                                    "radius": 20,
                                    "borderColor": "#FFFFFF", "borderWidth": 2
                                }
                            },
                            {
                                "type": "text",
                                "content": "Configuration réussie.",
                                "style": {
                                    "left": 20, "top": 56, 
                                    "width": 60, "height": 8,
                                    "size": 20, 
                                    "color": "#DDDDDD", 
                                    "bgColor": "#000000AA",
                                    "radius": 10
                                }
                            }
                        ]
                    }
                    # Envoi sans attendre de réponse
                    await websocket.send(json.dumps(success_msg, separators=(',', ':')))
                    # --- FIN SÉQUENCE ---

                    return self.async_create_entry(
                        title=f"Notify-it TV ({host})",
                        data={
                            "host": host,
                            "secret": data["secret"],
                            "device_id": device_id
                        }
                    )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout : Pas de clic sur la TV.")
        except Exception as e:
            _LOGGER.error(f"Erreur WebSocket : {e}")
            
        return None