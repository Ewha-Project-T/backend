from openai import OpenAI
import openai
from pydub import AudioSegment
import os
from dotenv import load_dotenv
import json

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

    def process_stt_result(self, text):
        result = text
        openai.api_key = os.getenv("OPENAI_API_KEY")

        prompt_message = (
            "Correct punctuations. Do not add or remove the script \n" + result
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt_message}],
                temperature=0,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            result = response.choices[0].message.content
            return result
        except Exception as e:
            print("Error during GPT-4 call:", e)
            return None

    
    def execute(self,filename):
        # Need to add path
        file_path = f"{os.environ['UPLOAD_PATH']}/{filename}.mp3"

        # Check if the file is larger than 25 MB
        if os.path.getsize(file_path) > 25 * 1024 * 1024:
            chunk_paths = self.split_audio(file_path)
            transcription = self.transcribe_chunks(chunk_paths)
        else:
            with open(file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )
        # transcription=transcription.replace(" ","。") #온점 누락 임시방편
        transcription=self.process_stt_result(transcription)
        data = {
            "text": transcription,
            "denotations": []
        }

        return json.dumps(data, indent=4, ensure_ascii=False)
