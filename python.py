import pyaudio
import numpy as np
import paho.mqtt.client as mqtt
import json
import time

# MQTT broker details
# This uses TLS (secure MQTT) with port 8883 and HiveMQ’s default TLS setup may want to use private Mosquitto broker later 
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 8883  # Secure port for TLS
MQTT_TOPIC = "branden/audiofft"

# PyAudio settings
CHUNK = 1024           # Number of audio samples per frame
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100           # Sampling rate in Hz

# Setup MQTT client with TLS
client = mqtt.Client()
client.tls_set()  # Use default system CA certs
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_start()

# Setup PyAudio stream
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("Streaming audio and publishing FFT data to MQTT...")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Compute FFT and convert to magnitude
        fft_data = np.abs(np.fft.fft(audio_data))[:CHUNK // 2]
        fft_data = np.round(fft_data / 100).astype(int)  # Scale and round for display

        # Serialize to JSON and publish
        payload = json.dumps(fft_data.tolist())
        client.publish(MQTT_TOPIC, payload)
        time.sleep(0.05) 
except KeyboardInterrupt:
    print("Stopping...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    client.loop_stop()
    client.disconnect()


