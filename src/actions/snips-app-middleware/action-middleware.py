#!/usr/bin/env python3

"""
This module contains a Snips app that act as a middleware beween intent and
slots to remap.
"""

from configparser import ConfigParser
from copy import deepcopy
import pathlib
import json
import logging

import toml
import paho.mqtt.client as mqtt


log = logging.getLogger("snips-middleware")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(filename)s:%(lineno)d %(levelname)-10s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler = logging.RotatingFileHandler('./middleware.log', encoding='utf-8')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
log.addHandler(handler)
log.propagate = False


CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"


class SnipsConfigParser(ConfigParser):
    def to_dict(self):
        return {
            section: {
                option_name: option
                for option_name, option in self.items(section) if option.strip()
            }
            for section in self.sections()
        }


def read_configuration_file(configuration_file):
    try:
        with pathlib.Path(configuration_file).open(encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser(delimiters=('='))
            conf_parser.optionxform = str
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error):
        return dict()


class AssistantMiddleware(object):
    """ This app reroute intent and slots from your Snips assistant.

    The rerouting is based on you config.ini
    """
    def __init__(self, debug=False):
        """Initialize the app."""
        # Get the MQTT host and port from /etc/snips.toml.
        self.config = read_configuration_file(CONFIG_INI)
        self.route_intents = self.config.get('route.intents')
        self.route_slots = self.config.get('route.slots')
        self.debug = debug
        try:
            mqtt_host_port = toml.load('/etc/snips.toml')['snips-common']['mqtt']
            mqtt_host, mqtt_port = mqtt_host_port.split(':')
            mqtt_port = int(mqtt_port)
        except (KeyError, ValueError):
            # If the mqtt key doesn't exist or doesn't have the correct format,
            # use the default values.
            mqtt_host = self.config['general'].get('mqtt_host', 'localhost')
            mqtt_port = int(self.config['general'].get('mqtt_port', 1883))
        mqtt_timeout = int(self.config['general'].get('mqtt_timeout', 5))

        self.client = mqtt.Client("snips-middleware")
        self.client.on_connect = self._subscribe_reroute
        if self.debug:
            log.info("debug mode activated")
            self.client.on_message = self.emit_rerouted_intent_debug

        self.client.connect(mqtt_host, mqtt_port, mqtt_timeout)
        self.client.loop_forever()

    def _subscribe_reroute(self, client, userdata, flags, rc):
        # remap intentA to intentB slot a to slot b
        if self.debug:
            self.client.subscribe("hermes/intent/#", 1)
        for intent_name, new_intent_name in self.route_intents.items():
            log.info('hook re route intent : %s => %s', intent_name, new_intent_name)
            client.message_callback_add(
                'hermes/intent/%s' % intent_name, self.emit_rerouted_intent)

    def emit_rerouted_intent_debug(self, client, userdata, message):
        log.debug("debug => captured intent")
        log.debug("topic: %s", str(message.topic))
        log.debug("payload: %s", str(message.payload))

    def emit_rerouted_intent(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode('utf8'))
        new_payload = deepcopy(payload)
        name = payload["intent"]["intentName"]
        rerouted_intent_name = self.route_intents[name]
        for slot_content in payload["slots"]:
            slot_name = slot_content['slotName']
            if slot_name in self.route_slots:
                new_slot_name = self.route_slots[slot_name]
                new_payload['slots'][new_slot_name] = slot_content
                del new_payload['slots'][slot_name]
        log.info("Intent %s detected with slots %s",
                 name,
                 [s['slotName'] for s in payload['slots']])
        log.info("Rerouted to Intent %s detected with slots %s",
                 rerouted_intent_name,
                 [s['slotName'] for s in new_payload['slots']])
        client.publish(
            'hermes/intent/%s' % rerouted_intent_name,
            json.dumps(new_payload)
        )


if __name__ == "__main__":
    AssistantMiddleware(debug=True)
