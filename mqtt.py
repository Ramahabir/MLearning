import paho.mqtt.client as mqtt

# MQTT Broker settings
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "emqx/esp32"

# Global variable to store the latest data
latest_data = {}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to broker")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print("❌ Connection failed with code", rc)

def on_message(client, userdata, msg):
    # Store latest message as decoded string, can be parsed as needed (JSON, CSV, etc.)
    try:
        latest_data['value'] = msg.payload.decode()
        latest_data['topic'] = msg.topic
    except Exception as e:
        print("❌ Error decoding message:", e)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()  # Non-blocking: runs MQTT loop in background

# Start the MQTT client as soon as this module is imported
start_mqtt()