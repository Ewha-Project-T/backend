from openai import OpenAI
from pydub import AudioSegment
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

class Original_stt:
    def split_audio(self,file_path, chunk_length_ms=60000):

        audio = AudioSegment.from_file(file_path)
        chunks = [
            audio[i : i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)
        ]

        chunk_paths = []
        for i, chunk in enumerate(chunks):
            chunk_path = f"{file_path}_chunk{i}.wav"
            chunk.export(chunk_path, format="wav")
            chunk_paths.append(chunk_path)

        return chunk_paths


    def transcribe_chunks(self,chunk_paths):

        combined_text = []
        for chunk_path in chunk_paths:
            with open(chunk_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )
                combined_text.append(transcript)
            os.remove(chunk_path)

        return " ".join(combined_text)

    def execute(self,filename):
        # Need to add path
        file_path = filename

        # Check if the file is larger than 25 MB
        if os.path.getsize(file_path) > 25 * 1024 * 1024:
            chunk_paths = self.split_audio(file_path)
            transcription = self.transcribe_chunks(chunk_paths)
        else:
            with open(file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )

        return transcription
