import time
import numpy as np
import simpleaudio as sa
import array
from pydub import AudioSegment
from pydub.utils import get_array_type
import paho.mqtt.client as mqtt
import sys

# ===== CONFIGURATION =====
MQTT_BROKER = "iot.cs.calvin.edu"
MQTT_PORT = 8883
MQTT_USERNAME = "cs326"
MQTT_PASSWORD = "piot"

BASS_TOPIC = "blh94/bass"
MID_TOPIC = "blh94/mid"
TREBLE_TOPIC = "blh94/treble"

FFT_SIZE = 2048
SAMPLE_RATE = 44100

BASS_CUTOFF = 200  # Hz
MID_CUTOFF = 2000  # Hz

# ===== MQTT SETUP =====
client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set()

def connect_mqtt():
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

# ===== AUDIO PROCESSING & STREAMING =====
def process_audio(audio_path):
    audio = AudioSegment.from_file(audio_path).set_channels(1).set_frame_rate(SAMPLE_RATE)
    array_type = get_array_type(audio.sample_width * 8)
    audio_array = array.array(array_type, audio._data)

    # Play the audio
    play_obj = sa.play_buffer(
        audio_array.tobytes(),
        num_channels=1,
        bytes_per_sample=audio.sample_width,
        sample_rate=SAMPLE_RATE
    )

    # Convert to float samples
    samples = np.array(audio_array).astype(np.float32)
    samples /= np.iinfo(audio_array.typecode).max

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

            bass_val = int(np.sum(bass))
            mid_val = int(np.sum(mid))
            treble_val = int(np.sum(treble))

            # Publish to MQTT
            client.publish(BASS_TOPIC, str(bass_val))
            client.publish(MID_TOPIC, str(mid_val))
            client.publish(TREBLE_TOPIC, str(treble_val))

            time.sleep(FFT_SIZE / SAMPLE_RATE)
            i += FFT_SIZE

    except KeyboardInterrupt:
        print("Interrupted. Stopping audio and MQTT.")
        play_obj.stop()

    client.loop_stop()
    client.disconnect()

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_audio_file>")
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    connect_mqtt()
    process_audio(audio_file_path)


# import paho.mqtt.client as mqtt
# import time
# import numpy as np
# import json

# # MQTT settings
# MQTT_BROKER = "iot.cs.calvin.edu"
# MQTT_PORT = 8883  # TLS port
# MQTT_USERNAME = "cs326"
# MQTT_PASSWORD = "piot"

# # Topics to subscribe to
# BASS_TOPIC = "blh94/bass"
# MID_TOPIC = "blh94/mid"
# TREBLE_TOPIC = "blh94/treble"

# # Store the latest values
# latest_values = {
#     "bass": 0,
#     "mid": 0,
#     "treble": 0
# }

# # Define callback functions for MQTT client
# def on_connect(client, userdata, flags, rc):
#     print(f"Connected with result code {rc}")
#     # Subscribe to topics once connected
#     client.subscribe(BASS_TOPIC)
#     client.subscribe(MID_TOPIC)
#     client.subscribe(TREBLE_TOPIC)

# def on_message(client, userdata, msg):
#     topic = msg.topic
#     payload = msg.payload.decode()
#     # Parse the comma-separated values and use the first value (or average, or sum, etc.)
#     values = [int(val) for val in payload.split(',') if val]

#     if not values:  # Handle empty lists
#         value = 0
#     else:
#         # You can choose how to handle multiple values:
#         value = values[0]
    
#     if topic == BASS_TOPIC:
#         latest_values["bass"] = value
#     elif topic == MID_TOPIC:
#         latest_values["mid"] = value
#     elif topic == TREBLE_TOPIC:
#         latest_values["treble"] = value
    
#     # Print the updated values (you can replace this with LED control code)
#     print(f"Bass: {latest_values['bass']}, Mid: {latest_values['mid']}, Treble: {latest_values['treble']}")
    
#     # TODO: Add your LED control code here based on the frequency values

# def main():
#     # Create MQTT client instance
#     client = mqtt.Client()
#     client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
#     # Set up TLS for secure connection
#     client.tls_set()  # Uses default system CA certificates
    
#     # Assign callback functions
#     client.on_connect = on_connect
#     client.on_message = on_message
    
#     # Connect to broker
#     print(f"Connecting to {MQTT_BROKER}...")
#     client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
#     # Start network loop
#     try:
#         client.loop_forever()
#     except KeyboardInterrupt:
#         print("Program interrupted by user")
#     finally:
#         client.disconnect()
#         print("Disconnected from broker")

# if __name__ == "__main__":
#     main()
