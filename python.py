import paho.mqtt.client as mqtt
import time
import numpy as np
import json

# MQTT settings
MQTT_BROKER = "iot.cs.calvin.edu"
MQTT_PORT = 8883  # TLS port
MQTT_USERNAME = "cs326"
MQTT_PASSWORD = "piot"

# Topics to subscribe to
BASS_TOPIC = "blh94/bass"
MID_TOPIC = "blh94/mid"
TREBLE_TOPIC = "blh94/treble"

# Store the latest values
latest_values = {
    "bass": 0,
    "mid": 0,
    "treble": 0
}

# Define callback functions for MQTT client
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to topics once connected
    client.subscribe(BASS_TOPIC)
    client.subscribe(MID_TOPIC)
    client.subscribe(TREBLE_TOPIC)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    # Parse the comma-separated values and use the first value (or average, or sum, etc.)
    values = [int(val) for val in payload.split(',') if val]

    if not values:  # Handle empty lists
        value = 0
    else:
        # You can choose how to handle multiple values:
        value = values[0]
    
    if topic == BASS_TOPIC:
        latest_values["bass"] = value
    elif topic == MID_TOPIC:
        latest_values["mid"] = value
    elif topic == TREBLE_TOPIC:
        latest_values["treble"] = value
    
    # Print the updated values (you can replace this with LED control code)
    print(f"Bass: {latest_values['bass']}, Mid: {latest_values['mid']}, Treble: {latest_values['treble']}")
    
    # TODO: Add your LED control code here based on the frequency values

def main():
    # Create MQTT client instance
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Set up TLS for secure connection
    client.tls_set()  # Uses default system CA certificates
    
    # Assign callback functions
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect to broker
    print(f"Connecting to {MQTT_BROKER}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Start network loop
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        client.disconnect()
        print("Disconnected from broker")

if __name__ == "__main__":
    main()
