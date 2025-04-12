##### LED_Driver #####
# This python program connects to an MQTT publisher and gatheres the published music frequencies
# The program then uses these frequencies to drive LEDs connected on a raspberry pi to create an audio visualizer
# Code is comprised of work from Prof. Derek Schurrman, and Caden Ziskie with the aid of ChatGPT

import time
import numpy as np
import simpleaudio as sa
import array
import busio
import paho.mqtt.client as mqtt
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
from pydub import AudioSegment
from pydub.utils import get_array_type

# Local import
import SECURITY

### Constants ###

# MQTT (not used here yet but placeholder)
PORT = 1883
QOS = 0
KEEPALIVE = 60
BROKER_AUTHENTICATION = True

BROKER = SECURITY.broker
TOPIC_B = SECURITY.topicB
TOPIC_M = SECURITY.topicM
TOPIC_T = SECURITY.topicT
USERNAME = SECURITY.username
PASSWORD = SECURITY.password

# Initialize I2C and PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 1000  # Set PWM frequency to 1kHz

# Audio file setup
AUDIO_FILE = "WAV/WhyTry.wav"  # You can change this to .wav or .ogg
NUM_LEDS_PER_GROUP = 5
FFT_SIZE = 2048
SAMPLE_RATE = 44100

# === Load and Prepare Audio ===
audio = AudioSegment.from_file(AUDIO_FILE).set_channels(1).set_frame_rate(SAMPLE_RATE)
array_type = get_array_type(audio.sample_width * 8)
audio_array = array.array(array_type, audio._data)

# Play the audio file
play_obj = sa.play_buffer(
    audio_array.tobytes(),
    num_channels=1,
    bytes_per_sample=audio.sample_width,
    sample_rate=SAMPLE_RATE
)

# Convert to normalized float samples for analysis
samples = np.array(audio_array).astype(np.float32)
samples /= np.iinfo(audio_array.typecode).max

# Frequency band mapping
BASS_CUTOFF = 200  # Hz
MID_CUTOFF = 2000  # Hz
NUM_FREQS = FFT_SIZE // 2

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

# === Main Loop ===
def main():
    try:
        i = 0
        while play_obj.is_playing() and i < len(samples):
            chunk = samples[i:i + FFT_SIZE]
            if len(chunk) < FFT_SIZE:
                break

            fft_result = np.abs(np.fft.rfft(chunk))
            freq_bins = np.fft.rfftfreq(FFT_SIZE, d=1.0 / SAMPLE_RATE)

            bass = fft_result[freq_bins <= BASS_CUTOFF]
            mid = fft_result[(freq_bins > BASS_CUTOFF) & (freq_bins <= MID_CUTOFF)]
            treble = fft_result[freq_bins > MID_CUTOFF]

            bass_brightness = normalize(bass[:NUM_LEDS_PER_GROUP])
            mid_brightness = normalize(mid[:NUM_LEDS_PER_GROUP])
            treble_brightness = normalize(treble[:NUM_LEDS_PER_GROUP])

            update_leds_for_band(0, bass_brightness)
            update_leds_for_band(NUM_LEDS_PER_GROUP, mid_brightness)
            update_leds_for_band(2 * NUM_LEDS_PER_GROUP, treble_brightness)

            time.sleep(FFT_SIZE / SAMPLE_RATE)
            i += FFT_SIZE

    except KeyboardInterrupt:
        print("Interrupted. Stopping audio and turning off LEDs.")
        play_obj.stop()

    finally:
        print("Shutting down. Turning off all LEDs.")
        for channel in range(NUM_LEDS_PER_GROUP * 3):
            pca.channels[channel].duty_cycle = 0


if __name__ == "__main__":
    main()

# ## Lab 7 ##
# # Callback when a connection has been established with the MQTT broker
# def on_connect(client, userdata, flags, reason_code, properties):
#     if reason_code == 0:
#         print(f'Connected to {BROKER} successful.')
#     else:
#         print(f'Connection to {BROKER} failed. Return code={rc}')

# # Callback when client receives a message from the broker
# # Use button message to turn LED on/off
# def on_message(client, data, msg):
#     print(f'MQTT message received -> topic:{msg.topic}, message:{msg.payload}')
#     if msg.topic == TOPIC:
#         return
#        # call main/led update

# # Setup MQTT client and callbacks 
# client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# if BROKER_AUTHENTICATION:
#     client.username_pw_set(USERNAME, password=PASSWORD)

# client.on_connect = on_connect
# client.on_message = on_message

# # Connect to MQTT broker and subscribe to the button topic
# client.connect(BROKER, PORT, KEEPALIVE)
# client.subscribe(TOPIC, qos=QOS)

# try:
#     client.loop_forever()
# except KeyboardInterrupt:
#     client.disconnect()
#     print('Done')
