# Music frequency processing code from LED_ALONE

import time
import numpy as np
import simpleaudio as sa
import array
from pydub import AudioSegment
from pydub.utils import get_array_type

# Audio file setup
AUDIO_FILE = "/home/Bazzite/Desktop/Ginger Root - Rikki - 06 Why Try.wav"  # will need to be replaced by the audio file upload from the website
FFT_SIZE = 2048
SAMPLE_RATE = 44100 # CD audio quality

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

            time.sleep(FFT_SIZE / SAMPLE_RATE)
            i += FFT_SIZE

            print(bass)
            print(mid)
            print(treble)

            # Publish stuff to the MQTT (either here directly, or via the webpage's JS)

    except KeyboardInterrupt: # Tie to pause/play button
        print("Interrupted. Stopping audio and turning off LEDs.")
        play_obj.stop()



# import pyaudio
# import numpy as np
# import paho.mqtt.client as mqtt
# import json
# import time

# # MQTT broker details
# # This uses TLS (secure MQTT) with port 8883 and HiveMQ’s default TLS setup may want to use private Mosquitto broker later 
# MQTT_BROKER = "broker.hivemq.com"
# MQTT_PORT = 8883  # Secure port for TLS
# MQTT_TOPIC = "branden/audiofft"

# # PyAudio settings
# CHUNK = 1024           # Number of audio samples per frame
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100           # Sampling rate in Hz

# # Setup MQTT client with TLS
# client = mqtt.Client()
# client.tls_set()  # Use default system CA certs
# client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
# client.loop_start()

# # Setup PyAudio stream
# p = pyaudio.PyAudio()
# stream = p.open(format=FORMAT,
#                 channels=CHANNELS,
#                 rate=RATE,
#                 input=True,
#                 frames_per_buffer=CHUNK)

# print("Streaming audio and publishing FFT data to MQTT...")

# try:
#     while True:
#         data = stream.read(CHUNK, exception_on_overflow=False)
#         audio_data = np.frombuffer(data, dtype=np.int16)

#         # Compute FFT and convert to magnitude
#         fft_data = np.abs(np.fft.fft(audio_data))[:CHUNK // 2]
#         fft_data = np.round(fft_data / 100).astype(int)  # Scale and round for display

#         # Serialize to JSON and publish
#         payload = json.dumps(fft_data.tolist())
#         client.publish(MQTT_TOPIC, payload)
#         time.sleep(0.05) 
# except KeyboardInterrupt:
#     print("Stopping...")
# finally:
#     stream.stop_stream()
#     stream.close()
#     p.terminate()
#     client.loop_stop()
#     client.disconnect()
