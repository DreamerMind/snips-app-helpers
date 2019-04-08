#!/usr/bin/env python3
"""
This module contains a Snips app that act as a middleware beween intent and
slots to remap.
"""

from collections import deque
import importlib
import json

import paho.mqtt.client as mqtt


CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {
            section: {
                option_name: option for option_name, option in self.items(section)
            }
            for section in self.sections()
        }

def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()



class AssistantMiddleware(object):
    """ This app reroute intent and slots from your Snips assistant.

    The rerouting is based on you config.ini
    """
    def __init__(self):
        """Initialize the app."""
        # Get the MQTT host and port from /etc/snips.toml.
        self.config = read_configuration_file(CONFIG_INI)
        self.route_intents = self.config.get('route.intents')
        self.route_slots = self.config.get('route.slots')
        try:
            mqtt_host_port = toml.load('/etc/snips.toml')['snips-common']['mqtt']
            mqtt_host, mqtt_port = mqtt_host_port.split(':')
            mqtt_port = int(mqtt_port)
        except (KeyError, ValueError):
            # If the mqtt key doesn't exist or doesn't have the correct format,
            # use the default values.
            mqtt_host = self.config['general'].get('mqtt_host', 'localhost')
            mqtt_port = self.config['general'].get('mqtt_port', 1883)
        mqtt_timeout = self.config['general'].get('mqtt_timeout', 60)

        self.client = mqtt.Client()
        self.client.on_connect = self._subscribe_reroute

        self.client.connect(mqtt_host, mqtt_port, mqtt_timeout)
        self.client.loop_forever()

    def _subscribe_reroute(self):
        # remap intentA to intentB slot a to slot b
        for intent in self.route_intents:
            client.message_callback_add('hermes/intent/%s' % intent_name,
                                        self.emit_rerouted_intent)

    def emit_rerouted_intent(self, client, userdata, flags, rc):
        pass
        # TODO
        # client.publish(
            # ...
        # )

    # TODO ASK all remap rule applied ?

if __name__ == "__main__":
    AssistantMiddleware()
