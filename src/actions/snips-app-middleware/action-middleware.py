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
import logging.handlers

import toml
import yaml

import paho.mqtt.client as mqtt


DEFAULT_TOML_PATH = "/etc/snips.toml"
ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"
SLOTS = "slots"
SLOT_NAME = "slotName"
INTENT_NAME = "intentName"
HERMES_INTENT = "hermes/intent/%s"
TO = "to"
INTENT = "intent"


log = logging.getLogger("snips-middleware")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(filename)s:%(lineno)d %(levelname)-10s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler = logging.handlers.RotatingFileHandler(
    "./middleware.log", encoding="utf-8"
)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
log.addHandler(handler)
log.propagate = False


class SnipsConfigParser(ConfigParser):
    def to_dict(self):
        return {
            section: {
                option_name: option
                for option_name, option in self.items(section)
                if option.strip()
            }
            for section in self.sections()
        }


def read_configuration_file(configuration_file):
    try:
        with pathlib.Path(configuration_file).open(
            encoding=ENCODING_FORMAT
        ) as f:
            conf_parser = SnipsConfigParser(delimiters=("="))
            conf_parser.optionxform = str
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error):
        return dict()


def load_route_table(path):
    with pathlib.Path(path).open("r") as fh:
        return yaml.load(fh, Loader=yaml.FullLoader)


class AssistantMiddleware(object):
    """ This app reroute intent and slots from your Snips assistant.

    The rerouting is based on you config.ini
    """

    def __init__(self, debug=False):
        """Initialize the app."""
        self.config = read_configuration_file(CONFIG_INI)["general"]
        self.routing_table = load_route_table(self.config.get("routing_table"))
        self.debug = self.config.get("debug", False)
        try:
            mqtt_host_port = toml.load(DEFAULT_TOML_PATH)["snips-common"][
                "mqtt"
            ]
            mqtt_host, mqtt_port = mqtt_host_port.split(":")
            mqtt_port = int(mqtt_port)
        except (KeyError, ValueError):
            # If the mqtt key doesn't exist or doesn't have the correct format,
            # use the default values.
            mqtt_host = self.config.get("mqtt_host", "localhost")
            mqtt_port = int(self.config.get("mqtt_port", 1883))
        mqtt_timeout = int(self.config.get("mqtt_timeout", 5))

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
            self.client.subscribe(HERMES_INTENT % "#", 1)
        for intent_name, intent_dic in self.routing_table.items():
            new_intent_name = intent_dic.get(TO)
            log.info(
                "hook re route intent : %s => %s", intent_name, new_intent_name
            )
            client.message_callback_add(
                HERMES_INTENT % intent_name, self.emit_rerouted_intent
            )
        log.info("started sucessfully")

    def emit_rerouted_intent_debug(self, client, userdata, message):
        log.debug("debug => captured intent")
        log.debug("topic: %s", str(message.topic))
        log.debug("payload: %s", str(message.payload))

    def emit_rerouted_intent(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode(ENCODING_FORMAT))
        new_payload = deepcopy(payload)
        name = payload[INTENT][INTENT_NAME]

        intent_routing_info = self.routing_table[name]
        rerouted_intent_name = intent_routing_info.get(TO)
        rerouted_intent_name = self.route_intents[name]
        for slot_content in payload[SLOTS]:
            slot_name = slot_content[SLOT_NAME]
            if slot_name in intent_routing_info[SLOTS]:
                new_slot_name = intent_routing_info[SLOTS][slot_name]
                new_payload[SLOTS][new_slot_name] = slot_content
                del new_payload[SLOTS][slot_name]
        log.info(
            "Intent %s detected with slots %s",
            name,
            [s[SLOT_NAME] for s in payload[SLOTS]],
        )
        log.info(
            "Rerouted to Intent %s detected with slots %s",
            rerouted_intent_name,
            [s[SLOT_NAME] for s in new_payload[SLOTS]],
        )
        client.publish(
            "hermes/intent/%s" % rerouted_intent_name, json.dumps(new_payload)
        )


if __name__ == "__main__":
    AssistantMiddleware(debug=True)
