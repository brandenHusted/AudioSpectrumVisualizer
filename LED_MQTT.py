##### LED_MQTT #####
# This python program connects to an MQTT publisher and gatheres the published music frequencies
# The program then uses these frequencies to drive LEDs connected on a raspberry pi to create an audio visualizer
# Code is comprised of work from Prof. Derek Schurrman, and Caden Ziskie with the aid of ChatGPT and ClaudeAI

import time
import numpy as np
import json
import busio
import paho.mqtt.client as mqtt
from adafruit_pca9685 import PCA9685
from board import SCL, SDA

# Local import
import SECURITY

### Constants ###

# MQTT Configuration
PORT = 1883
QOS = 0
KEEPALIVE = 60
BROKER_AUTHENTICATION = True

BROKER = SECURITY.broker
TOPIC_B = SECURITY.topicB  # Bass frequencies
TOPIC_M = SECURITY.topicM  # Mid frequencies
TOPIC_T = SECURITY.topicT  # Treble frequencies
USERNAME = SECURITY.username
PASSWORD = SECURITY.password

# Initialize I2C and PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 1000  # Set PWM frequency to 1kHz

# LED Configuration
NUM_LEDS_PER_GROUP = 5

# Global variables to store latest frequency data
bass_data = np.zeros(NUM_LEDS_PER_GROUP)
mid_data = np.zeros(NUM_LEDS_PER_GROUP)
treble_data = np.zeros(NUM_LEDS_PER_GROUP)

# Flag to indicate if new data has been received
new_data_received = False

# === LED Update Functions ===
def normalize(data):
    return (data / (np.max(data) if np.max(data) > 0 else 1)) * 0xFFF

def update_leds_for_band(led_group, brightness):
    max_brightness = 0xFFF
    total_energy = np.sum(brightness) / (NUM_LEDS_PER_GROUP * (max_brightness * 0.7))
    num_active_leds = min(int(total_energy * NUM_LEDS_PER_GROUP), NUM_LEDS_PER_GROUP)

    for i in range(NUM_LEDS_PER_GROUP):
        if i < num_active_leds:
            if total_energy > 0.8:
                brightness_value = max_brightness  # Full brightness
            elif total_energy > 0.6:
                brightness_value = int(max_brightness * 0.75)  # Bright
            elif total_energy > 0.4:
                brightness_value = int(max_brightness * 0.5)  # Medium
            else:
                brightness_value = int(max_brightness * 0.2)  # Dim
        else:
            brightness_value = 0
        pca.channels[led_group + i].duty_cycle = brightness_value

def update_all_leds():
    update_leds_for_band(0, bass_data)
    update_leds_for_band(NUM_LEDS_PER_GROUP, mid_data)
    update_leds_for_band(2 * NUM_LEDS_PER_GROUP, treble_data)

# === MQTT Callbacks ===
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f'Connected to {BROKER} successfully.')
        # Subscribe to all frequency topics
        client.subscribe(TOPIC_B, qos=QOS)
        client.subscribe(TOPIC_M, qos=QOS)
        client.subscribe(TOPIC_T, qos=QOS)
    else:
        print(f'Connection to {BROKER} failed. Return code={reason_code}')

def on_message(client, userdata, msg):
    global bass_data, mid_data, treble_data, new_data_received
    
    print(f'MQTT message received -> topic:{msg.topic}, message:{msg.payload}')
    
    try:
        # Parse the single value from the message
        value_str = msg.payload.decode('utf-8')
        
        try:
            # Try to convert the string to a float
            value = float(value_str)
            
            # Adjust for negative dB values from getFloatFrequencyData
            # Convert from typical range (-100 to 0 dB) to (0 to 1) for LED intensity
            # Normalize approximately -80dB (very quiet) to -30dB (loud)
            if value < -80:
                value = 0  # Below threshold, treat as silence
            elif value > -30:
                value = 1  # Very loud, max brightness
            else:
                # Linear mapping from -80dB to -30dB -> 0 to 1
                value = (value + 80) / 50
            
            # Create an array with the value distributed as a pattern
            # Create a bell curve or gradient pattern for visualization
            pattern = np.zeros(NUM_LEDS_PER_GROUP)
            
            # Center-weighted pattern (stronger in middle, weaker at edges)
            mid_point = (NUM_LEDS_PER_GROUP - 1) / 2
            for i in range(NUM_LEDS_PER_GROUP):
                distance = abs(i - mid_point)
                weight = 1.0 - (distance / mid_point) * 0.5  # Gentle slope
                pattern[i] = value * weight
                
        except ValueError:
            print(f"Could not convert value '{value_str}' to float, using zeros")
            pattern = np.zeros(NUM_LEDS_PER_GROUP)
        
        # Update the appropriate frequency band data
        if msg.topic == TOPIC_B:
            # Process bass frequency data
            bass_data = pattern * 0xFFF  # Scale to 12-bit PWM range
        elif msg.topic == TOPIC_M:
            # Process mid frequency data
            mid_data = pattern * 0xFFF
        elif msg.topic == TOPIC_T:
            # Process treble frequency data
            treble_data = pattern * 0xFFF
        
        new_data_received = True
        
    except Exception as e:
        print(f"Error processing message: {e}")

# === Main Function ===
def main():
    global new_data_received
    
    # Setup MQTT client and callbacks
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    if BROKER_AUTHENTICATION:
        client.username_pw_set(USERNAME, password=PASSWORD)
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect to MQTT broker
    try:
        client.connect(BROKER, PORT, KEEPALIVE)
        client.loop_start()  # Start MQTT loop in background thread
        
        print("Connected to MQTT broker. Waiting for frequency data...")
        
        try:
            while True:
                if new_data_received:
                    update_all_leds()
                    new_data_received = False
                time.sleep(0.01)  # Small delay to prevent CPU hogging
                
        except KeyboardInterrupt:
            print("Interrupted. Stopping LED driver.")
            
        finally:
            # Turn off all LEDs
            for channel in range(NUM_LEDS_PER_GROUP * 3):
                pca.channels[channel].duty_cycle = 0
            
            client.loop_stop()
            client.disconnect()
            print("MQTT client disconnected.")
            
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")

if __name__ == "__main__":
    main()
