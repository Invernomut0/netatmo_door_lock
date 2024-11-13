from collections import deque
import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE_NAME = "device_name"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE_NAME): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_name = config_entry.data[CONF_DEVICE_NAME]

    dehumidification_sensor = DehumidificationSensor(device_name)
    ndl_sensor = NDLSensor(device_name, dehumidification_sensor)
    humidity_alarm_sensor = HumidityAlarmSensor(device_name)
    #last_message_sensor = LastMessages(device_name)
    last_interesting_message_sensor = LastInterestingMessages(device_name)
    async_add_entities(
        [
            ndl_sensor,
            dehumidification_sensor,
            humidity_alarm_sensor,
            #last_message_sensor,
            last_interesting_message_sensor,
        ]
    )


class NDLSensor(Entity):
    def __init__(self, device_name, dehumidification_sensor):
        self._name = f"{device_name} Sensor"
        self._state = STATE_UNKNOWN
        self._device_name = device_name
        self._dehumidification_sensor = dehumidification_sensor

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        self.hass.bus.async_listen("myhome_message_event", self.handle_event)

    @callback
    def handle_event(self, event):
        data = event.data
        who = data.get("who")
        where = data.get("where")
        what = data.get("what")

        if who == 25 and where == "231":
            if what == 22:
                self._state = "off"
                self._dehumidification_sensor.set_state(
                    "off"
                )  # Chiamata a set_state per aggiornare Home Assistant
            elif what == 24:
                self._state = "on"
            self.async_write_ha_state()


class LastMessages(Entity):
    def __init__(self, device_name):
        self._name = f"{device_name} LastMessages"
        self._state = deque(maxlen=10)
        self._device_name = device_name

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        self.hass.bus.async_listen("myhome_message_event", self.handle_event)

    @callback
    def handle_event(self, event):
        msg = event.data.get("message")
        self._state.append(msg)
        self.async_write_ha_state()


class LastInterestingMessages(Entity):
    def __init__(self, device_name):
        self._name = f"{device_name} LastInterestingMessages"
        self._state = deque(maxlen=10)
        self._device_name = device_name

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        self.hass.bus.async_listen("myhome_message_event", self.handle_event)

    @callback
    def handle_event(self, event):
        data = event.data
        who = data.get("who")
        where = data.get("where")
        what = data.get("what")
        msg = data.get("message")

        if who == 1 or who == 25:
            self._state.append(msg)
            self.async_write_ha_state()


class DehumidificationSensor(Entity):
    def __init__(self, device_name):
        self._name = f"{device_name} Deumidificazione"
        self._state = STATE_UNKNOWN
        self._device_name = device_name

    def set_state(self, state):
        """Set the state of the sensor and update Home Assistant."""
        self._state = state
        self.async_write_ha_state()

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        self.hass.bus.async_listen("myhome_message_event", self.handle_event)

    @callback
    def handle_event(self, event):
        data = event.data
        who = data.get("who")
        where = data.get("where")
        what = data.get("what")

        if who == 1 and where in ["01", "02"]:
            if what == 1:
                self._state = "on"
            elif what == 0:
                self._state = "off"
            self.async_write_ha_state()


class HumidityAlarmSensor(Entity):
    def __init__(self, device_name):
        self._name = f"{device_name} Allarme Umidità"
        self._state = STATE_UNKNOWN
        self._device_name = device_name

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        self.hass.bus.async_listen("myhome_message_event", self.handle_event)

    @callback
    def handle_event(self, event):
        data = event.data
        who = data.get("who")
        where = data.get("where")
        what = data.get("what")

        if who == 1 and where == "03":
            if what == 0:
                self._state = "on"
            elif what == 1:
                self._state = "off"
            self.async_write_ha_state()
