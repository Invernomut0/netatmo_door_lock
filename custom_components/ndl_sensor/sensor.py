from collections import deque
import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt

from .utils import get_token, getNDL, open_door

_LOGGER = logging.getLogger(__name__)
DOMAIN = "ndl_sensor"

CONF_USERNAME = "Username"
CONF_PASSWORD = "Password"
CONF_DEVICE_NAME = "Netatmo Door Lock"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE_NAME): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Configura la piattaforma usando la configurazione YAML."""
    device_name = config.get(CONF_DEVICE_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    sensor = NDLSensor(device_name, username, password)
    async_add_entities([sensor], True)

    # Registra il servizio
    async def unlock_door(call):
        await sensor.async_set_state("unlock")

    hass.services.async_register(
        "ndl_sensor",  # domain
        "unlock_door",  # service name
        unlock_door,
    )

    return True  # Importante: restituisce True per indicare il successo


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform from config entry."""
    username = config_entry.data["Username"]
    password = config_entry.data["Password"]

    sensor = NDLSensor(hass, "Netatmo Door Lock", username, password)
    async_add_entities([sensor], True)

    # Registra il servizio
    async def unlock_door(call):
        await sensor.async_set_state("unlock")

    hass.services.async_register(DOMAIN, "unlock_door", unlock_door)
    return True


class NDLSensor(Entity):
    """Rappresentazione del sensore NDL."""

    def __init__(self, device_name, username, password):
        """Inizializza il sensore NDL."""
        self._name = device_name
        self._state = None
        self._available = True
        self._username = username
        self._password = password
        self._access_token = None
        self._bridge_id = None
        self._bridge = None
        self._id = None

    @property
    def bridge(self):
        """Restituisce l'ID della casa."""
        return self._bridge

    @property
    def bridge_id(self):
        """Restituisce l'ID della casa."""
        return self._bridge_id

    @property
    def id(self):
        """Restituisce l'ID del bridge."""
        return self._id

    @property
    def name(self):
        """Restituisce il nome del sensore."""
        return self._name

    @property
    def state(self):
        """Restituisce lo stato del sensore."""
        return self._state

    @property
    def available(self):
        """Restituisce se il sensore è disponibile."""
        return self._available

    async def async_update(self):
        """Aggiorna lo stato del sensore."""
        try:
            if not self._access_token:
                token_data = await self.hass.async_add_executor_job(
                    get_token, self._username, self._password
                )
                if token_data and "access_token" in token_data:
                    self._access_token = token_data["access_token"]
                else:
                    raise Exception("Impossibile ottenere il token di accesso")

            # TODO: Usa self._access_token per le chiamate API successive
            self._available = True
            ndl_data = await self.hass.async_add_executor_job(
                getNDL, self._access_token
            )
            if ndl_data and "body" in ndl_data:
                homes = ndl_data["body"].get("homes", [])
                if homes:
                    for home in homes:
                        modules = home.get("modules", [])
                        for module in modules:
                            if module.get("type") == "BNDL":
                                self._bridge = module.get("bridge")
                                self._bridge_id = module.get("id")
                                self._id = home.get("id")
                                self._state = "Locked"
                                break
            else:
                raise Exception("Impossibile ottenere i dati NDL")

        except Exception as ex:
            _LOGGER.error("Errore nell'aggiornamento del sensore: %s", ex)
            self._available = False
            self._access_token = None

    async def async_set_state(self, state):
        """Imposta lo stato della serratura."""
        try:
            if not self._access_token:
                token_data = await self.hass.async_add_executor_job(
                    get_token, self._username, self._password
                )
                if token_data and "access_token" in token_data:
                    self._access_token = token_data["access_token"]
                else:
                    raise Exception("Impossibile ottenere il token di accesso")

            result = await self.hass.async_add_executor_job(
                open_door,
                self._access_token,
                self._id,
                self._bridge,
                self._bridge_id,
                False,
            )

            if result:
                self._state = "Unlocked"
                self._available = True
                _LOGGER.info("Serratura aperta!")

                # Genera l'evento di apertura porta
                self.hass.bus.fire(
                    "ndl_door_opened",
                    {
                        "device_id": self._bridge,
                        "state": "Unlocked",
                        "friendly_name": self._name,
                        "timestamp": dt.utcnow().isoformat(),
                    },
                )
            else:
                raise Exception("Errore nel cambio di stato della serratura")

        except Exception as ex:
            _LOGGER.error("Errore nell'impostazione dello stato: %s", ex)
            self._available = False
            self._access_token = None
