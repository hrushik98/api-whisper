import os
import numpy as np
import pyaudio
from pydub import AudioSegment
from openai import OpenAI

# Make sure to replace "your_api_key" with your actual OpenAI API key
client = OpenAI(api_key = "sk-rzg3rnGB6YNhHo6hyKodT3BlbkFJ7Sg69CpcVuquzVe")

def get_transcription_from_whisper():
    # Set the audio parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 2048
    SILENCE_THRESHOLD = 300  # Silence threshold
    SPEECH_END_TIME = 1.0  # Time of silence to mark the end of speech

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Start Recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording...Waiting for speech to begin.")

    frames = []
    silence_frames = 0
    is_speaking = False
    total_frames = 0

    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        total_frames += 1

        # Convert audio chunks to integers
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Check if the user has started speaking
        if np.abs(audio_data).mean() > SILENCE_THRESHOLD:
            is_speaking = True

        # Detect if the audio chunk is silence
        if is_speaking:
            if np.abs(audio_data).mean() < SILENCE_THRESHOLD:
                silence_frames += 1
            else:
                silence_frames = 0

        # End of speech detected
        if is_speaking and silence_frames > int(SPEECH_END_TIME * (RATE / CHUNK)):
            print("End of speech detected.")
            break

    # Stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    print("Finished recording.")
    combined_audio_data = b''.join(frames)

    # Convert raw data to an AudioSegment object
    audio_segment = AudioSegment(
        data=combined_audio_data,
        sample_width=audio.get_sample_size(FORMAT),
        frame_rate=RATE,
        channels=CHANNELS
    )

    # Export as a compressed MP3 file with a specific bitrate
    audio_segment.export("output_audio_file.mp3", format="mp3", bitrate="32k")

    # It's a good practice to close the file after reading
    with open("output_audio_file.mp3", "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    # Return the transcript text
    to_dispaly = transcript.text
    from signal import signal, SIGTERM, SIGHUP, pause
    from rpi_lcd import LCD

    lcd = LCD()

    def safe_exit(signum,frame):
            exit(1)

    signal(SIGTERM, safe_exit)
    signal(SIGHUP, safe_exit)

    def display_transcription(transcription):
        try:
            max_line_length = 16  # Adjust the maximum characters per line as needed
            lines = [transcription[i:i + max_line_length] for i in range(0, len(transcription), max_line_length)]
            
            for i, line in enumerate(lines, start=1):
                lcd.text(f"{line}", i)
            
            pause()
        except KeyboardInterrupt:
            pass
        finally:
            lcd.clear()


    display_transcription(to_dispaly)



# Example usage of the function
if __name__ == '__main__':
    transcription = get_transcription_from_whisper()
    print("Transcript:", transcription)



