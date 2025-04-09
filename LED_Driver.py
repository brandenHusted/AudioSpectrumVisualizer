import time
import numpy as np
from pydub import AudioSegment
import simpleaudio as sa
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio

# Initialize I2C and PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 1000  # Set PWM frequency to 1kHz

# Audio file setup
AUDIO_FILE = "suckthis.ogg"  # Replace with your music file
NUM_LEDS_PER_GROUP = 5  # LEDs per frequency band
FFT_SIZE = 2048  # Number of samples per FFT calculation
SAMPLE_RATE = 44100  # Standard CD-quality sample rate

# Load the file and convert to raw data
audio = AudioSegment.from_file(AUDIO_FILE, format="ogg").set_frame_rate(SAMPLE_RATE).set_channels(1)
samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
samples /= np.max(np.abs(samples))  # Normalize audio data

# Play the audio file
play_obj = sa.play_buffer(samples, 1, audio.sample_width, SAMPLE_RATE)

# Frequency band mapping (approximate)
BASS_CUTOFF = 200  # Hz
MID_CUTOFF = 2000  # Hz
NUM_FREQS = FFT_SIZE // 2  # Number of FFT bins

# Normalize function to convert frequency band values to LED brightness
def normalize(data):
    return (data / (np.max(data) if np.max(data) > 0 else 1)) * 0xFFF

# Function to map frequency band to LEDs
def update_leds_for_band(led_group, brightness):
    max_brightness = 0xFFF  # Maximum PWM value (4095)
    
    # Increase sensitivity
    total_energy = np.sum(brightness) / (NUM_LEDS_PER_GROUP * (max_brightness * 0.7))  # More aggressive scaling
    
    num_active_leds = int(total_energy * NUM_LEDS_PER_GROUP)
    num_active_leds = min(num_active_leds, NUM_LEDS_PER_GROUP)  # Ensure we don't exceed LED count

    for i in range(NUM_LEDS_PER_GROUP):
        if i < num_active_leds:
            # Make brightness "jump" instead of being smooth
            if total_energy > 0.8:
                brightness_value = max_brightness  # Fully bright
            elif total_energy > 0.5:
                brightness_value = int(max_brightness * 0.5)  # Medium brightness
            else:
                brightness_value = int(max_brightness * 0.2)  # Dim brightness
        else:
            brightness_value = 0  # LED off
        
        # Immediately set LED brightness (no smoothing)
        pca.channels[led_group + i].duty_cycle = brightness_value

    time.sleep(0.0005)  # Faster updates for a more reactive effect

# Main loop to process audio and update LEDs
try:
    for i in range(0, len(samples), FFT_SIZE):
        chunk = samples[i:i + FFT_SIZE]  # Get a chunk of audio data

        # Apply FFT and get magnitudes
        fft_result = np.abs(np.fft.rfft(chunk))  # Compute FFT
        freq_bins = np.fft.rfftfreq(FFT_SIZE, d=1.0 / SAMPLE_RATE)  # Get frequency values

        # Split frequencies into bands
        bass = fft_result[freq_bins <= BASS_CUTOFF]  # Bass frequencies
        mid = fft_result[(freq_bins > BASS_CUTOFF) & (freq_bins <= MID_CUTOFF)]  # Mid frequencies
        treble = fft_result[freq_bins > MID_CUTOFF]  # Treble frequencies

        # Normalize the frequency bands to LED brightness
        bass_brightness = normalize(bass[:NUM_LEDS_PER_GROUP])  # Map bass to LED brightness
        mid_brightness = normalize(mid[:NUM_LEDS_PER_GROUP])  # Map mid to LED brightness
        treble_brightness = normalize(treble[:NUM_LEDS_PER_GROUP])  # Map treble to LED brightness

        # Update LEDs based on the frequency bands
        update_leds_for_band(0, bass_brightness)  # Update bass LEDs (group 1)
        update_leds_for_band(NUM_LEDS_PER_GROUP, mid_brightness)  # Update mid LEDs (group 2)
        update_leds_for_band(2 * NUM_LEDS_PER_GROUP, treble_brightness)  # Update treble LEDs (group 3)

        # Sync with playback
        time.sleep(FFT_SIZE / SAMPLE_RATE)  # Sync with audio playback

except KeyboardInterrupt:
    # Handle Ctrl+C gracefully and turn off all LEDs when interrupted
    print("Exiting... Turning off all LEDs.")
    for channel in range(NUM_LEDS_PER_GROUP * 3):
        pca.channels[channel].duty_cycle = 0
    play_obj.stop()

# import time
# import numpy as np
# from pydub import AudioSegment
# import simpleaudio as sa
# from adafruit_pca9685 import PCA9685
# from board import SCL, SDA
# import busio

# ### Gloabal Constants
# # Audio Setup
# AUDIO_FILE = "suckthis.ogg"  # Replace with your music file
# NUM_LEDS_PER_GROUP = 5  # LEDs per frequency band
# FFT_SIZE = 2048  # Number of samples per FFT calculation
# SAMPLE_RATE = 44100  # Standard CD-quality sample rate

# # Frequency band mapping (approximate)
# BASS_CUTOFF = 200  # Hz
# MID_CUTOFF = 2000  # Hz

# def PWM_Setup():
#     i2c = busio.I2C(SCL, SDA)
#     pca = PCA9685(i2c)
#     pca.frequency = 1000  # Set PWM frequency to 1kHz; controls the LED brightness
#     return pca

# def Audio_Setup(filePath):
#     # Load the file and convert to raw data
#     audio = AudioSegment.from_file(AUDIO_FILE, format="ogg").set_frame_rate(SAMPLE_RATE).set_channels(1)
#     samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
#     samples /= np.max(np.abs(samples))  # Normalize audio data
#     return samples, audio.sample_width

# # convert frequency values into LED brightness
# def normalize(data):
#     return (data / (np.max(data) if np.max(data) > 0 else 1)) * 0xFFF

# # Function to map frequency band to LEDs
# def update_leds_for_band(pca, freq_band, brightness):
#     max_brightness = 0xFFF  # Maximum PWM value (4095)
    
#     # Increase sensitivity
#     total_energy = np.sum(brightness) / (NUM_LEDS_PER_GROUP * (max_brightness * 0.7))  # More aggressive scaling
    
#     num_active_leds = int(total_energy * NUM_LEDS_PER_GROUP)
#     num_active_leds = min(num_active_leds, NUM_LEDS_PER_GROUP)  # Ensure we don't exceed LED count

#     for i in range(NUM_LEDS_PER_GROUP):
#         if i < num_active_leds:
#             # Make brightness "jump" instead of being smooth
#             if total_energy > 0.8:
#                 brightness_value = max_brightness  # Fully bright
#             elif total_energy > 0.5:
#                 brightness_value = int(max_brightness * 0.5)  # Medium brightness
#             else:
#                 brightness_value = int(max_brightness * 0.2)  # Dim brightness
#         else:
#             brightness_value = 0  # LED off
        
#         # Immediately set LED brightness (no smoothing)
#         pca.channels[led_group + i].duty_cycle = brightness_value

#     time.sleep(0.0005)  # Faster updates for a more reactive effect

# def Audio_Processing_N_LED_Update():
#     # Main loop to process audio and update LEDs
#     try:
#         for i in range(0, len(samples), FFT_SIZE):
#             chunk = samples[i:i + FFT_SIZE]  # Get a chunk of audio data

#             # Apply FFT and get magnitudes
#             fft_result = np.abs(np.fft.rfft(chunk))  # Compute FFT
#             freq_bins = np.fft.rfftfreq(FFT_SIZE, d=1.0 / SAMPLE_RATE)  # Get frequency values

#             # Split frequencies into bands
#             bass = fft_result[freq_bins <= BASS_CUTOFF]  # Bass frequencies
#             mid = fft_result[(freq_bins > BASS_CUTOFF) & (freq_bins <= MID_CUTOFF)]  # Mid frequencies
#             treble = fft_result[freq_bins > MID_CUTOFF]  # Treble frequencies

#             # Normalize the frequency bands to LED brightness
#             bass_brightness = normalize(bass[:NUM_LEDS_PER_GROUP])  # Map bass to LED brightness
#             mid_brightness = normalize(mid[:NUM_LEDS_PER_GROUP])  # Map mid to LED brightness
#             treble_brightness = normalize(treble[:NUM_LEDS_PER_GROUP])  # Map treble to LED brightness

#             # Update LEDs based on the frequency bands
#             update_leds_for_band(0, bass_brightness)  # Update bass LEDs (group 1)
#             update_leds_for_band(NUM_LEDS_PER_GROUP, mid_brightness)  # Update mid LEDs (group 2)
#             update_leds_for_band(2 * NUM_LEDS_PER_GROUP, treble_brightness)  # Update treble LEDs (group 3)

#             # Sync with playback
#             time.sleep(FFT_SIZE / SAMPLE_RATE)  # Sync with audio playback

#     except KeyboardInterrupt:
#         # Handle Ctrl+C gracefully and turn off all LEDs when interrupted
#         print("Exiting... Turning off all LEDs.")
#         for channel in range(NUM_LEDS_PER_GROUP * 3):
#             pca.channels[channel].duty_cycle = 0
#         play_obj.stop()

# if __name__ == "__main__":
#     pca = PWM_Setup()
#     samples, sample_width = Audio_Setup(AUDIO_FILE)

#     # Play the audio file
#     play_obj = sa.play_buffer(samples, 1, audio.sample_width, SAMPLE_RATE)

#     Audio_Processing_N_LED_Update(pca, samples)

#     play_obj,wait_done()

# # Frequency band mapping (approximate)
# #NUM_FREQS = FFT_SIZE // 2  # Number of FFT bins