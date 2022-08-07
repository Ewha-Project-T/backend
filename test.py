import azure.cognitiveservices.speech as speechsdk

def from_file():
    speech_config = speechsdk.SpeechConfig(subscription="18c20da6bd3447238718e3a5738a5ea1", region="koreacentral")
    audio_input = speechsdk.AudioConfig(filename="uploads/75a47ca8-b3ac-42a7-8815-6520e0ccc36b.wav")
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = speech_recognizer.recognize_once_async().get()
    print(result.text)

from_file()
