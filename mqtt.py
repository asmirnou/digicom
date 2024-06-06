import logging
import json
from os import environ
from queue import SimpleQueue, Empty
import paho.mqtt.client as mqtt

event_queue = SimpleQueue()


def publish(stop_event, prefix):
    try:
        logger = logging.getLogger(__name__)

        client = mqtt.Client()
        client.enable_logger(logger)
        client.connect_async(host=environ.get('MQTT_HOST', 'localhost'))
        client.loop_start()

        while not stop_event.is_set():
            try:
                event = event_queue.get(timeout=1)

                client.publish(topic=prefix + '/events', payload=json.dumps(event), qos=1)
            except Empty:
                continue
    finally:
        stop_event.set()