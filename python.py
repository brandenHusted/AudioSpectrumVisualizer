import numpy as np
import json
import asyncio
import websockets
import wave
from pydub import AudioSegment
import tempfile
import base64

# WebSocket clients storage
clients = set()

async def audio_stream(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "upload":
                mp3_data = data["mp3_data"]
                await process_mp3_and_send_fft(mp3_data, websocket)
    finally:
        clients.remove(websocket)

async def process_mp3_and_send_fft(mp3_data, websocket):
    # Convert base64 MP3 data to a WAV file
    decoded_mp3 = base64.b64decode(mp3_data)

    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp_mp3:
        tmp_mp3.write(decoded_mp3)
        tmp_mp3.flush()
        audio = AudioSegment.from_mp3(tmp_mp3.name)

    # Convert to WAV format
    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmp_wav:
        audio.export(tmp_wav.name, format="wav")
        
        # Read WAV file
        wf = wave.open(tmp_wav.name, "rb")
        RATE = wf.getframerate()
        CHUNK = 1024  # Frames per buffer
        
        while True:
            data = wf.readframes(CHUNK)
            if not data:
                break

            # Convert audio to numpy array
            audio_samples = np.frombuffer(data, dtype=np.int16)

            # Compute FFT
            fft_data = np.abs(np.fft.rfft(audio_samples))
            fft_json = json.dumps(fft_data.tolist())

            # Send FFT data
            if websocket.open:
                await websocket.send(fft_json)
            await asyncio.sleep(0.05)  # Small delay to simulate streaming

# Start WebSocket Server
async def main():
    start_server = await websockets.serve(audio_stream, "0.0.0.0", 8765)
    print("WebSocket server started at ws://0.0.0.0:8765")
    await start_server.wait_closed()

# Run the event loop
if __name__ == "__main__":
    asyncio.run(main())
