#!/usr/bin/python3
""" DIYHA asset
    Send server information to MQTT broker
"""

# The MIT License (MIT)
#
# Copyright (c) 2021 parttimehacker@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging.config
import time
import paho.mqtt.client as mqtt

from pkg_classes.testmodel import TestModel
from pkg_classes.topicmodel import TopicModel
from pkg_classes.whocontroller import WhoController
from pkg_classes.configmodel import ConfigModel
from pkg_classes.statusmodel import StatusModel

# Start logging and enable imported classes to log appropriately.

LOGGING_FILE = '/usr/local/asset/logging.ini'
logging.config.fileConfig( fname=LOGGING_FILE, disable_existing_loggers=False )
LOGGER = logging.getLogger(__name__)
LOGGER.info('Application started')

# get the command line arguements

CONFIG = ConfigModel(LOGGING_FILE)

# Location is used to create the switch topics

TOPIC = TopicModel()  # Location MQTT topic
TOPIC.set(CONFIG.get_location())

# Set up who message handler from MQTT broker and wait for client.

WHO = WhoController(LOGGING_FILE)

# process diy/system/test development messages

TEST = TestModel(LOGGING_FILE)

# Process MQTT messages using a dispatch table algorithm.

def system_message(client, msg):
    """ Log and process system messages. """
    # pylint: disable=unused-argument
    LOGGER.info(msg.topic + " " + msg.payload.decode('utf-8'))
    if msg.topic == 'diy/system/test':
        TEST.on_message(msg.payload)
    elif msg.topic == 'diy/system/who':
        if msg.payload == b'ON':
            WHO.turn_on()
        else:
            WHO.turn_off()


#  A dictionary dispatch table is used to parse and execute MQTT messages.

TOPIC_DISPATCH_DICTIONARY = {
    "diy/system/test":
        {"method": system_message},
    "diy/system/who":
        {"method": system_message}
}


def on_message(client, userdata, msg):
    """ dispatch to the appropriate MQTT topic handler """
    # pylint: disable=unused-argument
    TOPIC_DISPATCH_DICTIONARY[msg.topic]["method"](client, msg)


def on_connect(client, userdata, flags, rc_msg):
    """ Subscribing in on_connect() means that if we lose the connection and
        reconnect then subscriptions will be renewed.
    """
    # pylint: disable=unused-argument
    client.subscribe("diy/system/test", 1)
    client.subscribe("diy/system/who", 1)


def on_disconnect(client, userdata, rc_msg):
    """ Subscribing on_disconnect() tilt """
    # pylint: disable=unused-argument
    client.connected_flag = False
    client.disconnect_flag = True


if __name__ == '__main__':

    # Setup MQTT handlers then wait for timed events or messages

    CLIENT = mqtt.Client()
    CLIENT.on_connect = on_connect
    CLIENT.on_disconnect = on_disconnect
    CLIENT.on_message = on_message

    # initilze the Who client for publishing.

    WHO.set_client(CLIENT)

    # command line argument for the switch mode - motion activated is the default

    CLIENT.connect(CONFIG.get_broker(), 1883, 60)
    CLIENT.loop_start()

    time.sleep(2) # let MQTT stuff initialize

    # initialize status monitoring

    STATUS = StatusModel(CLIENT)
    STATUS.start()

    # Loop forever waiting for motion

    while True:
        time.sleep(2.0)
