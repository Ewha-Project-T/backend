from curses import delay_output
from multiprocessing.pool import ThreadPool
from threading import Thread
import azure.cognitiveservices.speech as speechsdk
import uuid, re, time, os, requests

from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize

def simultaneous_stt(filename):
    myaudio = AudioSegment.from_file(filename)  # 경로 변경 필요
    sound, startidx, endidx, silenceidx = indexing(myaudio)
    # stt, pause_result, delay_result = do_faststt(sound, myaudio, startidx, endidx, silenceidx)
    jobid = do_faststt(sound, myaudio, startidx, endidx, silenceidx)



    result = {'textFile': '', 'timestamps': [], 'annotations': []}
    for i in range(len(sound)):
        result['timestamps'].append({'start': startidx[i], 'end': endidx[i]})

    p = re.compile('(\w\(filler\)|\w+\s\w+\(backtracking\))')
    fidx = []
    while (True):
        f = p.search(stt)
        if f == None:
            break
        fidx.append([f.start(), f.end()])
        stt = re.sub("(\(filler\)|\(backtracking\))", "", stt, 1)

    for i in range(len(fidx)):
        if stt[fidx[i][0]] == '음' or stt[fidx[i][0]] == '그' or stt[fidx[i][0]] == '어':
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
        else:
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

    pidx = []
    indx = -1
    while True:
        indx = stt.find('\n', indx + 1)
        if indx == -1:
            break
        pidx.append(indx)
    for i in range(len(pidx)): # pause, delay 구분 없이 pause 로 통일
        result['annotations'].append({'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': silenceidx[i]})

    result['textFile'] = stt

    return result

def indexing(myaudio):
    print("detecting silence")
    dBFS = myaudio.dBFS
    sound = silence.detect_nonsilent(
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16)  # 1초 이상의 silence
    sound = [[(start), (stop)] for start, stop in sound]
    startidx = []
    endidx = []
    silenceidx = []
    print("indexing")
    for i in range(0, len(sound)):
        startidx.append(sound[i][0])
        endidx.append(sound[i][1] + 200)
        if i < len(sound) - 1:
            silenceidx.append(sound[i + 1][0] - sound[i][1])
    return sound, startidx, endidx, silenceidx

def process_stt_result(stt):
    result = stt
    result = re.sub('니다', '니다. ', result)
    result = re.sub('까요', '까요. ', result)
    result = result.split()
    for i in range(len(result)):
        if result[i] == '음' or result[i] == '그' or result[i] == '어':
            result[i] = result[i] + "(filler)"
        if len(result) > 1 and result[i-1][0] == result[i][0] and result[i-1] in result[i]:
            result[i] = result[i] + "(backtracking)"
        elif len(result) > 1 and result[i-1][0] == result[i][0] and len(result[i-1]) <= len(result[i]):
            result[i] = result[i] + "(backtracking)"

    result = ' '.join(result)
    return result

def do_stt(sound, myaudio, startidx, endidx, silenceidx):
    flag = True
    text = ''
    delay_result = 0
    pause_result = 0
    filetmp = uuid.uuid4()
    for i in range(len(sound)):
        filepath = f"./uploads/{filetmp}.wav"
        myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
        # To recognize speech from an audio file, use `filepath` instead of `use_default_microphone`:
        stt = speech_recognize_continuous_from_file(filepath)
        text = text + stt
        sentences = sent_tokenize(stt)
        for sentence in sentences:
            # print(sentence)
            if sentence.endswith('.'):
                flag = True
            else:
                flag = False
        if i < len(sound) - 1:
            if flag == False:
                # print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                text = text+'\n'
                pause_result += silenceidx[i]
            else:
                # 통역 개시 지연구간
                # print("(delay: " + str(silenceidx[i]) + "sec)")
                text = text+'\n'
                delay_result += silenceidx[i]
        os.remove(filepath)
    return text, pause_result, delay_result

JOBS = {}

def do_faststt(sound, myaudio, startidx, endidx, silenceidx):
    domain = os.getenv("DOMAIN", "https://ewha.ltra.cc")

    files = []
    for i in range(len(sound)):
        filetmp = uuid.uuid4()
        filepath = f"uploads/{filetmp}.wav"
        myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
        files += [ domain + "/" + filepath ]

    webhook_res = requests.post(
        "https://koreacentral.api.cognitive.microsoft.com/speechtotext/v3.0/transcriptions",
        headers={
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": "18c20da6bd3447238718e3a5738a5ea1"
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

    result_link = webhook_res["links"]["files"]
    jobid = str(uuid.uuid4())
    JOBS[jobid] = {
        "url": result_link,
        "sound": sound,
        "silenceidx": silenceidx
    }
    # requests.get(
    #     result_link,
    #     headers={ "Ocp-Apim-Subscription-Key": "18c20da6bd3447238718e3a5738a5ea1" }
    # ).json()
    return jobid
    
    # pause_result = 0
    # delay_result = 0
    # for job in jobs:
    #     result = job.get()
    #     text = "".join(result[0])
    #     pause_result += result[1]
    #     delay_result += result[2]

    # return text, pause_result, delay_result

def speech_recognize_continuous_from_file(filename):
    # myaudio = AudioSegment.from_file(filename)  # 경로 변경 필요
    # sound, startidx, endidx, silenceidx = indexing(myaudio)
    speech_config = speechsdk.SpeechConfig(subscription="18c20da6bd3447238718e3a5738a5ea1", region="koreacentral", speech_recognition_language="ko-KR")
    audio_config = speechsdk.audio.AudioConfig(filename=filename)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    done = False

    def stop_cb(evt):
        """callback that stops continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        speech_recognizer.stop_continuous_recognition()
        nonlocal done
        done = True

    result = []
    def handle_final_result(evt):
        result.append(evt.result.text)

    speech_recognizer.recognized.connect(handle_final_result)
    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
    speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
    # speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    # speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    # speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

    # print("Printing all results:")
    return result[0]

print(simultaneous_stt("./uploads/dd1ac59d-eea4-4e79-ba04-26afffbcb3ca.wav"))