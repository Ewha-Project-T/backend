from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize

import os
import requests
import re


#한국어버전시작
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

def basic_indexing(filename):
    filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.wav"
    myaudio = AudioSegment.from_file(filepath)
    dBFS = myaudio.dBFS
    sound = silence.detect_nonsilent(
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16, seek_step=100)  # 1초 이상의 silence
    sound = [[(start), (stop)] for start, stop in sound]
    startidx = []
    endidx = []
    silenceidx = []
    for i in range(0, len(sound)):
        startidx.append(sound[i][0])
        endidx.append(sound[i][1] + 200)
        if i < len(sound) - 1:
            silenceidx.append(sound[i + 1][0] - sound[i][1])
    return sound, startidx, endidx, silenceidx, myaudio

def basic_do_stt(res,sound,silenceidx):
    flag = True
    text = ''
    delay_result = 0
    pause_result = 0
    pause_idx=[]
    values = res["values"]
    tmp_textFile= ['' for i in range(len(values))]
    for i in range(len(values)):
        tmp_seq=values[i]["name"]
        tmp_seq = re.findall("-?\d+", tmp_seq)
        if not tmp_seq:#report.json 처리
            continue
        tmp_seq=int(tmp_seq[0])
        kind = values[i]["kind"]
        if kind != "Transcription":
            continue

        recog = requests.get(values[i]["links"]["contentUrl"]).json()
        if(not recog["combinedRecognizedPhrases"]):
            continue
        stt = process_stt_result(recog["combinedRecognizedPhrases"][0]["lexical"])
        text = stt
        sentences = sent_tokenize(stt)
        for sentence in sentences:
            if sentence.endswith('.'):
                flag = True
            else:
                flag = False
        if i < len(sound) - 1:
            if flag == False:
                print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                text = text+'\n'
                pause_idx.append(silenceidx[i])
            else:
                # 통역 개시 지연구간
                print("(delay: " + str(silenceidx[i]) + "sec)")
                text = text+'\n'
                delay_result += silenceidx[i]
        tmp_textFile[tmp_seq] = text

    tmp_text=''.join(tmp_textFile)                
    return tmp_text, pause_result, delay_result, pause_idx

def basic_annotation_stt(result,stt,pause_idx):
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
            result['annotations'].append({'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
        else:
            result['annotations'].append({'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

    pidx = [m.start(0) + 1 for m in re.finditer('[^\.^\n]\n', stt)]
    for i in range(len(pidx)):  # pause, delay 구분 없이 pause 로 통일
        result['annotations'].append({'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': pause_idx[i]})

    if stt.endswith("\n"):
        stt = stt[:-1]
    result['textFile']=stt   
    return result
#한국어버전 끝

#일본어버전 시작
def simultaneous_stt(filename):
    myaudio = AudioSegment.from_file(
        f'{filename}')  # 경로 변경 필요
    length, startidx, endidx, silenceidx = indexing(myaudio)
    stt, pause_result, delay_result, pause_idx, start_idx, end_idx = do_stt(
        length, myaudio, startidx, endidx, silenceidx)

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
        if stt[fidx[i][0]] == 'え' or stt[fidx[i][0]] == 'ま':
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
        if stt[fidx[i][0]] == 'あの' or stt[fidx[i][0]] == 'えと' or stt[fidx[i][0]] == 'その':
            result['annotations'].append(
                {'start': fidx[i][0], 'end': fidx[i][0] + 2, 'type': 'FILLER'})
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


def indexing(myaudio):
    print("detecting silence")
    dBFS = myaudio.dBFS
    sound = silence.detect_nonsilent(
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16, seek_step=100)  # 1초 이상의 silence
    sound = [[(start), (stop)] for start, stop in sound]
    length = len(sound)
    startidx = []
    endidx = []
    silenceidx = []
    duration = 0
    i=0
    print("indexing")
    while i < len(sound):
        duration = sound[i][1] - sound[i][0]
        if duration < 2000:
            if i == 0:
                length = length - 1
                startidx.append(sound[i][0])
                endidx.append(sound[i+1][1] + 200)
                if len(sound) > 2:
                    silenceidx.append(sound[i+2][0] - sound[i+1][1])
                i = i+1
            else:
                length = length - 1
                endidx[-1] = sound[i][1] + 200
                if i < len(sound) - 1:
                    silenceidx[-1] = sound[i + 1][0] - sound[i][1]
        else: 
            startidx.append(sound[i][0])
            endidx.append(sound[i][1] + 200)
            if i < len(sound) - 1:
                silenceidx.append(sound[i + 1][0] - sound[i][1])
        i = i+1
    return length, startidx, endidx, silenceidx




def process_stt_result(stt):
    result = stt
    for i in range(len(result)):
        if result[i] == 'え' or result[i] == 'ま' or result[i] == 'あの' or result[i] == 'えと' or result[i] == 'その':
            result[i] = result[i] + "(filler)"
        if len(result) > 1 and result[i-1][0] == result[i][0] and result[i-1] in result[i]:
            result[i] = result[i] + "(backtracking)"
        # elif len(result) > 1 and result[i-1][0] == result[i][0] and len(result[i-1]) <= len(result[i]):
        #     result[i] = result[i] + "(backtracking)" #앞뒤단어의 첫글자가 같을때
    result = ' '.join(result)
    return result



def req_upload(file, completion,fullText=True):

    invoke_url = 'https://clovaspeech-gw.ncloud.com/external/v1/4257/c2761d7a201319106f45d6557ef2a076e6285af96da7e4da3fce4c910a2e7174'

    request_body = {
        'language': 'ja',
        'completion': completion,
        'fullText': fullText,
        'noiseFiltering' : False
    }
    headers = {
        'Accept': 'application/json;UTF-8',
        'X-CLOVASPEECH-API-KEY': '3edd2f729d7544d9b77f157fd6256ab9'
    }
#     print(json.dumps(request_body, ensure_ascii=False).encode('UTF-8'))
    files = {
        'media': open(file, 'rb'),
        'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
    }
    response = requests.post(headers=headers, url=invoke_url + '/recognizer/upload', files=files)
    return response



def do_stt(length, myaudio, startidx, endidx, silenceidx):

    
    flag = True
    text = ''
    delay_result = 0
    pause_result = 0
    pause_idx = []
    start_idx = []
    end_idx = []
    for i in range(length):
        myaudio[startidx[i]:endidx[i]].export("temp.wav", format="wav")
        # To recognize speech from an audio file, use `filename` instead of `use_default_microphone`:
        with open('temp.wav', 'rb') as payload:
            response = req_upload(file='temp.wav', completion='sync')
            if response.status_code != 200:
                # raise RuntimeError("API server does not response correctly")
                try:
                    response.raise_for_status()
                    text = response.text.strip()
                    if len(text) > 0:
                        print("Recognized text: ", text)
                    else:
                        print("No speech detected")
                except requests.exceptions.HTTPError as e:
                    print("HTTP error: ", e)
                except requests.exceptions.ConnectionError as e:
                    print("Error connecting to server: ", e)
                except requests.exceptions.Timeout as e:
                    print("Timeout error: ", e)
                except requests.exceptions.RequestException as e:
                    print("Error: ", e)
            dic = json.loads(response.text)
            # print(dic)
            if dic.get("result") == "COMPLETED":
                # tmp = dic.get("segments")
                tagger = fugashi.Tagger()
                words= [word.surface for word in tagger(dic['text'])]
                stt = process_stt_result(words)
                # print(stt)
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
                if i < length - 1:
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
#일본어버전 끝