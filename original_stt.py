import json
import os
import re

import nltk
import requests
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment, silence

nltk.download("punkt")


def simultaneous_stt(filename):
    myaudio = AudioSegment.from_file(
        f'tmp/{filename}')  # 경로 변경 필요
    sound, startidx, endidx, silenceidx = indexing(myaudio)
    stt, pause_result, delay_result, pause_idx, start_idx, end_idx = do_stt(
        sound, myaudio, startidx, endidx, silenceidx)

    result = {'textFile': '', 'timestamps': [], 'annotations': []}
    for i in range(len(start_idx)):
        result['timestamps'].append({'start': start_idx[i], 'end': end_idx[i]})

    stt = re.sub("\n{2,}","\n",stt)

    if stt.startswith("\n"):
        stt = stt[1:]
    
    p = re.compile('(\w\(filler\)|\w+\s\w+\(backtracking\))')
    fidx = []
    while (True):
        f = p.search(stt)
        if f == None:
            break
        fidx.append([f.start(), f.end()])
        stt = re.sub("(\(filler\)|\(backtracking\))", "", stt, 1)

    for i in range(len(fidx)):
        if stt[fidx[i][0]] == '음' or stt[fidx[i][0]] == '그' or stt[fidx[i][0]] == '어' or stt[fidx[i][0]] == '아':
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
        else:
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACK'})

    pidx = [m.start(0) + 1 for m in re.finditer('[^\.^\n]\n', stt)]
    for i in range(len(pidx)):  # pause, delay 구분 없이 pause 로 통일
        result['annotations'].append(
            {'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': pause_idx[i]})

    if stt.endswith("\n"):
        stt = stt[:-1]

    result['textFile'] = stt

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
        stt, pause_result, delay_result, pause_idx = do_stt(
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
        if text[fidx[i][0]] == '음' or text[fidx[i][0]] == '그' or text[fidx[i][0]] == '어' or text[fidx[i][0]] == '아':
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
        else:
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACK'})

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
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16, seek_step=100)  # 1초 이상의 silence
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
        if result[i] == '음' or result[i] == '그' or result[i] == '어' or result[i] == '아':
            result[i] = result[i] + "(filler)"
        if len(result) > 1 and result[i-1][0] == result[i][0] and result[i-1] in result[i]:
            result[i] = result[i] + "(backtracking)"
        elif len(result) > 1 and result[i-1][0] == result[i][0] and len(result[i-1]) <= len(result[i]):
            result[i] = result[i] + "(backtracking)"

    result = ' '.join(result)
    return result


def do_stt(sound, myaudio, startidx, endidx, silenceidx):
    url = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=ko-KR&format=detailed"

    headers = {
      'Content-type': 'audio/wav;codec="audio/pcm";',
      'Ocp-Apim-Subscription-Key': '5cba94119d774c0f9e5b20eacf98ff54',
    #   'Authorization': Bearer ACCESS_TOKEN'
    }

    flag = True
    text = ''
    delay_result = 0
    pause_result = 0
    pause_idx = []
    start_idx = []
    end_idx = []
    for i in range(len(sound)):
        myaudio[startidx[i]:endidx[i]].export("temp.wav", format="wav")
        # To recognize speech from an audio file, use `filename` instead of `use_default_microphone`:
        with open('temp.wav', 'rb') as payload:
            response = requests.request(
                "POST", url, headers=headers, data=payload)
            if response.status_code != 200:
                raise RuntimeError("API server does not response correctly")
            dic = json.loads(response.text)
            if dic.get("RecognitionStatus") == "Success":
                tmp = dic.get("NBest")
                stt = process_stt_result(tmp[0].get("Lexical"))
                text = text + stt
                if len(stt)>0:
                    start_idx.append(startidx[i])
                    end_idx.append(endidx[i])
                sentences = sent_tokenize(stt)
                for sentence in sentences:
                    print(sentence)
                    if sentence.endswith('.'):
                        flag = True
                    else:
                        flag = False
                if i < len(sound) - 1:
                    if flag == False:
                        print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                        text = text+'\n'
                        pause_result += silenceidx[i]
                        pause_idx.append(silenceidx[i])
                    else:
                        # 통역 개시 지연구간
                        print("(delay: " + str(silenceidx[i]) + "sec)")
                        text = text+'\n'
                        delay_result += silenceidx[i]
            else:
                continue
        os.remove("temp.wav")
    return text, pause_result, delay_result, pause_idx, start_idx, end_idx
