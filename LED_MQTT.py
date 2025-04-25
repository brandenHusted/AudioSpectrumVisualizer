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

# Thresholds for frequency bands (adjust these based on your observations)
BASS_MIN = 150    # Threshold for silence (below this is silent)
BASS_MAX = 250    # Threshold for maximum intensity for bass

MID_MIN = 50     # Threshold for silence
MID_MAX = 175     # Threshold for maximum intensity for mids

TREBLE_MIN = 25  # Threshold for silence
TREBLE_MAX = 100  # Threshold for maximum intensity for treble

# Flag to indicate if new data has been received
new_data_received = False

# === LED Update Functions ===
def update_leds_for_band(led_group, intensity_value):
    """
    Update LEDs for a frequency band based on intensity value (0-1)
    Using a stepped approach - LEDs light up progressively as intensity increases
    """
    max_brightness = 0xFFF  # 12-bit PWM full brightness
    
    # Determine how many LEDs to light based on intensity
    # Map intensity 0-1 to 0-NUM_LEDS_PER_GROUP
    num_leds_to_light = min(NUM_LEDS_PER_GROUP, round(intensity_value * NUM_LEDS_PER_GROUP))
    
    # Set brightness levels - in this implementation:
    # - First LEDs to light up are at lower positions (0, 1, etc.)
    # - Later LEDs (higher positions) only light up at higher intensities
    # - Each LED gets progressively brighter as intensity increases
    for i in range(NUM_LEDS_PER_GROUP):
        if i < num_leds_to_light:
            # Calculate brightness for this specific LED
            # More dramatic effect: earlier LEDs brighter, later LEDs dimmer
            position_factor = 1.0 - (i / NUM_LEDS_PER_GROUP) * 0.5
            
            # Calculate LED-specific brightness (0-1 scale)
            led_brightness = position_factor * intensity_value
            
            # Scale to PWM range and apply
            pca.channels[led_group + i].duty_cycle = int(led_brightness * max_brightness)
        else:
            # Turn off LEDs beyond the active count
            pca.channels[led_group + i].duty_cycle = 0

def update_all_leds():
    """Update all LED groups based on current frequency data"""
    # Calculate the maximum value for each band to determine active LEDs
    bass_intensity = np.max(bass_data)
    mid_intensity = np.max(mid_data)
    treble_intensity = np.max(treble_data)
    
    # Update each LED group
    update_leds_for_band(0, bass_intensity)
    update_leds_for_band(NUM_LEDS_PER_GROUP, mid_intensity)
    update_leds_for_band(2 * NUM_LEDS_PER_GROUP, treble_intensity)

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
            
            # Map the value to an appropriate intensity based on the frequency band
            if msg.topic == TOPIC_B:
                # Process bass frequency data
                intensity = map_value_to_intensity(value, BASS_MIN, BASS_MAX)
                # Create intensity array with a pattern
                bass_data = create_intensity_pattern(intensity)
                
            elif msg.topic == TOPIC_M:
                # Process mid frequency data
                intensity = map_value_to_intensity(value, MID_MIN, MID_MAX)
                mid_data = create_intensity_pattern(intensity)
                
            elif msg.topic == TOPIC_T:
                # Process treble frequency data
                intensity = map_value_to_intensity(value, TREBLE_MIN, TREBLE_MAX)
                treble_data = create_intensity_pattern(intensity)
            
            new_data_received = True
            
        except ValueError:
            print(f"Could not convert value '{value_str}' to float")
            
    except Exception as e:
        print(f"Error processing message: {e}")

def map_value_to_intensity(value, min_threshold, max_threshold):
    """
    Maps the dB value to an intensity between 0 and 1
    - Values below min_threshold are considered silence (0)
    - Values above max_threshold are considered maximum intensity (1)
    - Values in between are mapped linearly
    """
    # Handle values outside the valid range
    if value <= min_threshold:
        return 0.0
    if value >= max_threshold:
        return 1.0
    
    # Linear mapping from min_threshold to max_threshold -> 0 to 1
    normalized = (value - min_threshold) / (max_threshold - min_threshold)
    
    # Apply exponential curve for more dramatic effect (sound levels are logarithmic)
    intensity = normalized ** 1.5  # Adjust exponent to tune response
    
    return intensity

def create_intensity_pattern(intensity):
    """
    Creates an array of intensity values for the LEDs based on overall intensity
    Using a pattern that increases intensity from edges to center
    """
    pattern = np.zeros(NUM_LEDS_PER_GROUP)
    
    # Calculate center position
    mid_point = (NUM_LEDS_PER_GROUP - 1) / 2
    
    # Create intensity pattern - stronger in middle, weaker at edges
    for i in range(NUM_LEDS_PER_GROUP):
        # Calculate distance from center position (0 to 1 scale)
        distance = abs(i - mid_point) / mid_point
        
        # Create bell curve effect - higher in middle
        weight = 1.0 - distance ** 2  # Quadratic falloff for more dramatic effect
        
        # Set final intensity for this position
        pattern[i] = intensity * weight
    
    return pattern

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
