import paho.mqtt.publish as publish
import datetime
import time
import logging

from acoupi import config_mqtt

# Setup the main logger
logging.basicConfig(
    filename="heartbeat.log",
    filemode="w",
    format="%(levelname)s - %(message)s",
    level=logging.INFO,
)

def get_heartbeat():

    datetime_now = datetime.datetime.now()
    payload = "" + datetime_now.strftime("%Y-%m-%d") + "T" + datetime_now.strftime("%X")

    try:
        mqtt_auth = { 'username': config_mqtt.DEFAULT_MQTT_CLIENT_USER, 'password': config_mqtt.DEFAULT_MQTT_CLIENT_PASS }
        publish.single(config_mqtt.DEFAULT_MQTT_TOPIC, payload, hostname=config_mqtt.DEFAULT_MQTT_HOST, port=config_mqtt.DEFAULT_MQTT_PORT, auth=mqtt_auth)
    except:
        logging.info("No connection")
    
    return

get_heartbeat()