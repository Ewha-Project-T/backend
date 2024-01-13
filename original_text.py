import os
from pydub import AudioSegment
from dotenv import load_dotenv
import json
import openai
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")

class Original_stt:
    def split_audio(self, file_path, chunk_length_ms=60000):
        try:
            audio = AudioSegment.from_file(file_path)
            chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

            chunk_paths = []
            for i, chunk in enumerate(chunks):
                chunk_path = f"{file_path}_chunk{i}.wav"
                chunk.export(chunk_path, format="wav")
                chunk_paths.append(chunk_path)

            print(f"Audio split into {len(chunk_paths)} chunks.")
            return chunk_paths
        except Exception as e:
            print(f"Error during audio splitting: {e}")
            return None

    def transcribe_chunks(self, chunk_paths):
        if chunk_paths is None:
            print("No chunk paths provided for transcription.")
            return None

        combined_text = []
        for i, chunk_path in enumerate(chunk_paths):
            try:
                with open(chunk_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file, response_format="text"
                    )
                    combined_text.append(transcript)
                    print(f"Chunk {i} transcribed successfully.")
                os.remove(chunk_path)
            except Exception as e:
                print(f"Error during transcription of chunk {i}: {e}")

        return " ".join(combined_text)

    def process_stt_result(self, text):
        if text is None or text.strip() == "":
            print("No text or invalid text for GPT-4 processing.")
            return None

        prompt_message = "Correct punctuations. Do not add or remove the script \n" + text
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt_message}],
                temperature=0,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            corrected_text = response.choices[0].message.content
            print("Text processed with GPT-4 successfully.")
            return corrected_text
        except Exception as e:
            print(f"Error during GPT-4 call: {e}")
            return None

    def execute(self, filename):
        try:
            file_path = f"{os.environ['UPLOAD_PATH']}/{filename}.mp3"

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"No file found at {file_path}")

            print("Starting transcription process...")
            if os.path.getsize(file_path) > 25 * 1024 * 1024:
                print("Large file detected. Splitting audio...")
                chunk_paths = self.split_audio(file_path)
                transcription = self.transcribe_chunks(chunk_paths)
            else:
                with open(file_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file, response_format="text"
                    )

            if transcription:
                corrected_transcription = self.process_stt_result(transcription)
                if corrected_transcription:
                    data = {"text": corrected_transcription, "denotations": []}
                    return json.dumps(data, indent=4, ensure_ascii=False)
                else:
                    print("Failed to process transcription text with GPT-4.")
                    return None
            else:
                print("Failed to transcribe audio.")
                return None
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None