import asyncio
import csv
from datetime import datetime
from shazamio import Shazam
import pyaudio
import wave
import os

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10

details = {}
is_song_found = False

async def find_song():
    global details, is_song_found
    shazam = Shazam()

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Listening... Press 'q' to stop.")
    frames = []
    while not is_song_found:
        print('11')
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        print('1122')
        # Write the accumulated data to a temporary WAV file
        wf = wave.open('temp.wav', 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        print('112233')
        # Use the temporary WAV file for recognition
        out = await shazam.recognize('temp.wav')
        print('11223344')
        if out.get("track"):
            details = out
            print(f"Song recognized: {details['track']['title']} by {details['track']['subtitle']}")
            save_to_csv(details['track']['title'], details['track']['subtitle'])
            is_song_found = True
            break
        print('1122334455')
        # Reset the frames list for the next iteration
        frames = []

    # Cleanup
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Remove temporary file
    if os.path.exists('temp.wav'):
        os.remove('temp.wav')

def save_to_csv(title, artist):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    with open('song_history.csv', mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([timestamp, title, artist])

try:
    asyncio.run(find_song())
except KeyboardInterrupt:
    print('Exiting...')