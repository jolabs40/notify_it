import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# On déclare les plateformes : Notification ET Binary Sensor (pour l'état)
PLATFORMS = ["notify", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configuration de l'intégration."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Déchargement propre."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)