import json
import os
import re
import uuid
from flask_jwt_extended import get_jwt_identity
import requests
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment, silence

from server import db
from ..model import Stt

JOBS = {}

def simultaneous_stt(filename):
    myaudio = AudioSegment.from_file(filename)  # 경로 변경 필요
    sound, startidx, endidx, silenceidx = indexing(myaudio)
    
    return do_stt(sound, myaudio, startidx, endidx, silenceidx)

def stt_getJobResult(jobid):
    if jobid not in JOBS:
        return False

    url = JOBS[jobid]["url"]
    sound = JOBS[jobid]["sound"]
    startidx = JOBS[jobid]["startidx"]
    endidx = JOBS[jobid]["endidx"]
    silenceidx = JOBS[jobid]["silenceidx"]

    res = requests.get(
        url,
        headers={ "Ocp-Apim-Subscription-Key": os.environ['OCP_APIM_SUBSCRIPTION_KEY'] }
    ).json()

    if len(res["values"]) == 0:
        return False

    result = {'textFile': '', 'timestamps': [], 'annotations': []}
    for i in range(len(sound)):
        result['timestamps'].append({'start': startidx[i], 'end': endidx[i]})

    flag = True
    text = ''
    delay_result = 0
    pause_result = 0

    values = res["values"]
    for i in range(len(values)):
        kind = values[i]["kind"]
        if kind != "Transcription":
            continue

        recog = requests.get(values[i]["links"]["contentUrl"]).json()
        stt = process_stt_result(recog["recognizedPhrases"][0]["nBest"][0]["lexical"])
        text += stt
        sentences = sent_tokenize(stt)
        for sentence in sentences:
            # print(sentence)
            if sentence.endswith('.'):
                flag = True
            else:
                flag = False
        if i < len(sound) - 1:
            if flag == False:
                print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                text = text+'\n'
                pause_result += silenceidx[i]
            else:
                # 통역 개시 지연구간
                print("(delay: " + str(silenceidx[i]) + "sec)")
                text = text+'\n'
                delay_result += silenceidx[i]

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

        result['textFile'] += stt

    return result


def sequential_stt(filename, index):
    myaudio = AudioSegment.from_file(
        f'tmp/{filename}')  # 경로 변경 필요
    result = {'textFile': '', 'timestamps': [], 'annotations': []}
    silenceidxs = []
    temp = []
    for i in range(len(index)):
        audio_part = myaudio[index[i][0]:index[i][1]]
        sound, startidx, endidx, silenceidx = indexing(audio_part)
        silenceidxs.append(silenceidx)
        stt, pause_result, delay_result = do_stt(
            sound, audio_part, startidx, endidx, silenceidx)

        for j in range(len(sound)):
            result['timestamps'].append(
                {'start': startidx[j]+index[i][0], 'end': endidx[j]+index[i][0]})

        temp.append(stt)

    text = '\n\n'.join(temp)
    p = re.compile('(\w\(filler\)|\w+\s\w+\(backtracking\))')
    fidx = []
    while (True):
        f = p.search(text)
        if f == None:
            break
        fidx.append([f.start(), f.end()])
        text = re.sub("(\(filler\)|\(backtracking\))", "", text, 1)

    for i in range(len(fidx)):
        if text[fidx[i][0]] == '음' or text[fidx[i][0]] == '그' or text[fidx[i][0]] == '어':
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
        else:
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

    idx = [m.start(0) + 1 for m in re.finditer('[^\\n]\\n[^\\n]', text)]
    for i in range(len(idx)):  # pause, delay 구분 없이 pause 로 통일
        result['annotations'].append(
            {'start': idx[i], 'end': idx[i]+1, 'type': 'Pause', 'duration': silenceidxs[i]})

    result['textFile'] = text

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


# def do_stt(sound, myaudio, startidx, endidx, silenceidx):
#     url = os.getenv("STT_API_URL")

#     headers = {
#         'Content-type': 'audio/wav;codec="audio/pcm";',
#         'Ocp-Apim-Subscription-Key': os.getenv("OCP_APIM_SUBSCRIPTION_KEY"),
#     }

#     flag = True
#     text = ''
#     delay_result = 0
#     pause_result = 0
#     filetmp = uuid.uuid4()
#     for i in range(len(sound)):
#         myaudio[startidx[i]:endidx[i]].export(f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav", format="wav")
#         # To recognize speech from an audio file, use `filename` instead of `use_default_microphone`:
#         with open(f"{filetmp}.wav", 'rb') as payload:
#             response = requests.request(
#                 "POST", url, headers=headers, data=payload)
#             if response.status_code != 200:
#                 raise RuntimeError("API server does not response correctly")
#             dic = json.loads(response.text)
#             if dic.get("RecognitionStatus") == "Success":
#                 tmp = dic.get("NBest")
#                 stt = process_stt_result(tmp[0].get("Lexical"))
#                 text = text + stt
#                 sentences = sent_tokenize(stt)
                # for sentence in sentences:
                #     # print(sentence)
                #     if sentence.endswith('.'):
                #         flag = True
                #     else:
                #         flag = False
                # if i < len(sound) - 1:
                #     if flag == False:
                #         # print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                #         text = text+'\n'
                #         pause_result += silenceidx[i]
                #     else:
                #         # 통역 개시 지연구간
                #         # print("(delay: " + str(silenceidx[i]) + "sec)")
                #         text = text+'\n'
                #         delay_result += silenceidx[i]
#             else:
#                 continue
#         os.remove(f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav")
#     return text, pause_result, delay_result

def do_stt(sound, myaudio, startidx, endidx, silenceidx):
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
        "startidx": startidx,
        "endidx": endidx,
        "silenceidx": silenceidx
    }
    return jobid

def mapping_sst_user(homework, file):
    userinfo = get_jwt_identity()
    stt = Stt(user_no=userinfo["user_no"], homework_no=homework, wav_file=file)
    db.session.add(stt)
    db.session.commit

def is_stt_userfile(homework, file) -> bool:
    userinfo = get_jwt_identity()
    stt = Stt.query.filter_by(user_no=userinfo["user_no"], homework_no=homework, wav_file=file).first()
    if stt is None:
        return False
    return True

def remove_userfile(homework, file) -> bool:
    userinfo = get_jwt_identity()
    stt = Stt.query.filter_by(user_no=userinfo["user_no"], homework_no=homework, wav_file=file)
    if stt is None:
        return False
    try:
        os.unlink(f"{os.getenv['UPLOAD_PATH']}/{file}")
    except:
        pass
    stt.delete()
    db.session.commit
    return True

def get_userfile():
    userinfo = get_jwt_identity()
    stt = Stt.query.filter_by(user_no=userinfo["user_no"]).all()
    if stt is None:
        return False
    return stt