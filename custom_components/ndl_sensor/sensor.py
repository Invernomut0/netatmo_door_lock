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
CONF_PASSWORD = "password"

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
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    # Ottieni il token di accesso
    token_data = await hass.async_add_executor_job(get_token, username, password)
    if not token_data or "access_token" not in token_data:
        _LOGGER.error("Impossibile ottenere il token di accesso")
        return False

    access_token = token_data["access_token"]

    # Ottieni i dati NDL
    ndl_data = await hass.async_add_executor_job(getNDL, access_token)
    if not ndl_data or "body" not in ndl_data:
        _LOGGER.error("Impossibile ottenere i dati NDL")
        return False

    sensors = []
    homes = ndl_data["body"].get("homes", [])
    for home in homes:
        modules = home.get("modules", [])
        for module in modules:
            if module.get("type") == "BNDL":
                sensor = NDLSensor(
                    module.get("name", "Netatmo Door Lock"),  # Usa il nome del modulo
                    username,
                    password,
                    home.get("id"),
                    module.get("bridge"),
                    module.get("id"),
                )
                sensors.append(sensor)

    if not sensors:
        _LOGGER.error("Nessun sensore BNDL trovato")
        return False

    async_add_entities(sensors, True)

    # Registra il servizio
    async def unlock_door(call):
        entity_id = call.data.get("entity_id")
        for sensor in sensors:
            if sensor.entity_id == entity_id:
                await sensor.async_set_state("unlock")
                break

    hass.services.async_register(DOMAIN, "unlock_door", unlock_door)
    return True


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform from config entry."""
    username = config_entry.data["Username"]
    password = config_entry.data["Password"]

    # Simile a async_setup_platform
    token_data = await hass.async_add_executor_job(get_token, username, password)
    if not token_data or "access_token" not in token_data:
        return False

    access_token = token_data["access_token"]
    ndl_data = await hass.async_add_executor_job(getNDL, access_token)
    if not ndl_data or "body" not in ndl_data:
        return False

    sensors = []
    homes = ndl_data["body"].get("homes", [])
    for home in homes:
        modules = home.get("modules", [])
        for module in modules:
            if module.get("type") == "BNDL":
                sensor = NDLSensor(
                    module.get("name", "Netatmo Door Lock"),
                    username,
                    password,
                    home.get("id"),
                    module.get("bridge"),
                    module.get("id"),
                )
                sensors.append(sensor)

    if sensors:
        async_add_entities(sensors, True)

        async def unlock_door(call):
            entity_id = call.data.get("entity_id")
            for sensor in sensors:
                if sensor.entity_id == entity_id:
                    await sensor.async_set_state("unlock")
                    break

        hass.services.async_register(DOMAIN, "unlock_door", unlock_door)
        return True
    return False


class NDLSensor(Entity):
    """Rappresentazione del sensore NDL."""

    def __init__(self, device_name, username, password, home_id, bridge, bridge_id):
        """Inizializza il sensore NDL."""
        self._name = device_name
        self._state = "Locked"
        self._available = True
        self._username = username
        self._password = password
        self._access_token = None
        self._bridge_id = bridge_id
        self._bridge = bridge
        self._id = home_id
        self._lock_state = {}  # Aggiungi dizionario per tracciare lo stato individuale

    @property
    def icon(self):
        """Restituisce l'icona del sensore."""
        return "mdi:lock"

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
                self._lock_state[self._bridge_id] = "Unlocked"  # Usa l'ID univoco del bridge
                self._state = self._lock_state[self._bridge_id]
                self._available = True
                _LOGGER.info(f"Serratura {self._name} aperta!")

                self.hass.bus.fire(
                    "ndl_door_opened",
                    {
                        "device_id": self._bridge,
                        "state": self._state,
                        "friendly_name": self._name,
                        "timestamp": dt.utcnow().isoformat(),
                    },
                )
            else:
                raise Exception(f"Errore nel cambio di stato della serratura {self._name}")

        except Exception as ex:
            _LOGGER.error(f"Errore nell'impostazione dello stato per {self._name}: {ex}")
            self._available = False
            self._access_token = None
