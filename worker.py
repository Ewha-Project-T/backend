from celery import Celery
from pydub import AudioSegment, silence
import os
import uuid
import requests
import time

BROKER = os.environ['REDIS_BACKEND']
CELERY_RESULT_BACKEND = os.environ['REDIS_BACKEND']
celery = Celery("tasks", broker=BROKER, backend=CELERY_RESULT_BACKEND)

@celery.task(bind=True)
def do_stt_work(self, filename):
    self.update_state(state='INDEXING')

    filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.wav"
    myaudio = AudioSegment.from_file(filepath)

    dBFS = myaudio.dBFS
    sound = silence.detect_nonsilent(
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16)  # 1초 이상의 silence
    sound = [[(start), (stop)] for start, stop in sound]
    startidx = []
    endidx = []
    silenceidx = []
    for i in range(0, len(sound)):
        startidx.append(sound[i][0])
        endidx.append(sound[i][1] + 200)
        if i < len(sound) - 1:
            silenceidx.append(sound[i + 1][0] - sound[i][1])

    self.update_state(state='STT')
    
    domain = os.getenv("DOMAIN", "https://ewha.ltra.cc")

    files = []
    local_file = []
    for i in range(len(sound)):
        filetmp = uuid.uuid4()
        filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
        myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
        files += [ domain + "/" + filepath ]
        local_file += [ filepath ]
    
    webhook_res = requests.post(
        os.environ["STT_URL"],
        headers={
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": os.environ["STT_KEY"]
        },
        json={
            "contentUrls": files,
            "properties": {
                "diarizationEnabled": False,
                "wordLevelTimestampsEnabled": True,
                "punctuationMode": "DictatedAndAutomatic",
                "profanityFilterMode": "Masked"
            },
            "locale": "ko-KR",
            "displayName": "Transcription of file using default model for en-US"
        }
    ).json()

    url = webhook_res["links"]["files"]
    res = { 'values': [] }
    while len(res["values"]) == 0:
        res = requests.get(
            url,
            headers={ "Ocp-Apim-Subscription-Key": os.environ['STT_KEY'] }
        ).json()

        time.sleep(1)
    
    for file in local_file:
        os.unlink(file)

    self.update_state(state='DONE')

    return res, sound, startidx, endidx, silenceidx, filename

@celery.task(bind=True)
def do_sequential_stt_work(self, filename, index):
    filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.wav"
    myaudio = AudioSegment.from_file(filepath)

    sounds = []
    silenceidxs = []
    startidxs= []
    endidxs = []
    temp = []
    for i in range(len(index)):
        audio_part = myaudio[index[i][0]:index[i][1]]
        dBFS = myaudio.dBFS
        sound = silence.detect_nonsilent(audio_part, min_silence_len=1000, silence_thresh=dBFS - 16)
        sound = [[(start), (stop)] for start, stop in sound]
        startidx = []
        endidx = []
        silenceidx = []
        for i in range(0, len(sound)):
            startidx.append(sound[i][0])
            endidx.append(sound[i][1] + 200)
            if i < len(sound) - 1:
                silenceidx.append(sound[i + 1][0] - sound[i][1])
        sounds += [ sound ]
        startidxs += [ startidx ]
        endidxs += [ endidx ]
        silenceidxs += [ silenceidx ]

        self.update_state(state='STT')
    
        domain = os.getenv("DOMAIN", "https://ewha.ltra.cc")

        files = []
        local_file = []
        for i in range(len(sound)):
            filetmp = uuid.uuid4()
            filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
            myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
            files += [ domain + "/" + filepath ]
            local_file += [ filepath ]
        
        webhook_res = requests.post(
            os.environ["STT_URL"],
            headers={
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": os.environ["STT_KEY"]
            },
            json={
                "contentUrls": files,
                "properties": {
                    "diarizationEnabled": False,
                    "wordLevelTimestampsEnabled": True,
                    "punctuationMode": "DictatedAndAutomatic",
                    "profanityFilterMode": "Masked"
                },
                "locale": "ko-KR",
                "displayName": "Transcription of file using default model for en-US"
            }
        ).json()

        url = webhook_res["links"]["files"]
        res = { 'values': [] }
        while len(res["values"]) == 0:
            res = requests.get(
                url,
                headers={ "Ocp-Apim-Subscription-Key": os.environ['STT_KEY'] }
            ).json()

            time.sleep(1)
        
        for file in local_file:
            os.unlink(file)

        temp += [ res ]

    return temp, sounds, startidxs, endidxs, silenceidxs, filename