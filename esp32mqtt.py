import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "emqx/esp32"
latest_data = {}

def on_connect(client, userdata, flags, rc):
    print("Connected: ", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    # print("Raw payload:", msg.payload)
    try:
        payload = msg.payload.decode()
        latest_data.update(json.loads(payload))  # if JSON
        # print("Parsed data:", latest_data)
    except Exception as e:
        latest_data['value'] = payload
        print("Fallback to raw string:", payload)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

start_mqtt()
