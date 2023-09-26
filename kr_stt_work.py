#new_(gpt 사용+json output)

from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize

import os
import requests
import re
import fugashi
import json
import time
import uuid
import openai #openai 라이브러리 install 필요
import ast 

class KorStt:
    def process_stt_result(self,stt):
        result = stt
        openai.api_key = "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" # api key

        response = openai.ChatCompletion.create(
            model="gpt-4", messages=[{"role": "user", "content": "Mark '(filler)' on the rigth side of hesitating expressions such as '음', '아', or '그' (example: 음(filler)). And put '(cancellation)' on the rigth side of repeating expressions that can be removed, such as '다릅' in '다릅 틀립니다.', '있었' in '있었 있었습니다' or '학회에서' in '경제학회에서 학회에서도'. (example: 있었(cancellation) 있었습니다 .)  /n" + result}]
        )

        result = response.choices[0].message.content
        return result

    def indexing(self, myaudio):
        dBFS = myaudio.dBFS
        sound = silence.detect_nonsilent(
            myaudio, min_silence_len=1000, silence_thresh=dBFS - 16, seek_step=100)  # 1초 이상의 silence
        sound = [[(start), (stop)] for start, stop in sound]
        length = len(sound)
        startidx = []
        endidx = []
        silenceidx = []
        for i in range(0, len(sound)):
            startidx.append(sound[i][0])
            endidx.append(sound[i][1] + 200)
            if i < len(sound) - 1:
                silenceidx.append(sound[i + 1][0] - sound[i][1])
        return sound, startidx, endidx, silenceidx


    def do_stt(self, sound, myaudio, startidx, endidx, silenceidx):
        url = os.environ["STT_URL"]

        headers = {
        'Content-type': 'audio/wav;codec="audio/pcm";',
        'Ocp-Apim-Subscription-Key': os.environ["STT_KEY"],
        #   'Authorization': Bearer ACCESS_TOKEN'
        }

        flag = True
        text = ''
        delay_result = 0
        pause_result = 0
        pause_idx = []
        start_idx = []
        end_idx = []
        pause_final = ''
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
                    stt = dic.get("DisplayText")
                    text = text + stt
                    if len(stt)>0:
                        start_idx.append(startidx[i])
                        end_idx.append(endidx[i])
                    sentences = sent_tokenize(stt)
                    for sentence in sentences:
                        pause_final += sentence
                        pause_final += ' '

                    if i < len(sound) - 1:
                        pause_final += "(pause)" #"(pause: " + str(silenceidx[i]/1000)+"sec) "
                        text = text+' '
                        pause_result += silenceidx[i]
                        pause_idx.append(silenceidx[i])
                else:
                    continue
            os.remove("temp.wav")
        return pause_final, text, pause_result, delay_result, pause_idx, start_idx, end_idx

    def basic_annotation_stt(self, result,stt,pause_final,pause_idx):
        p = re.compile('(\w\(filler\)|\w+\s\w+\(cancellation\))')
        aidx = []

        while (True):
            f = p.search(stt)
            if f == None:
                break
            aidx.append([f.start(), f.end()])
            stt = re.sub("(\(filler\)|\(cancellation\))", "", stt, 1)

        for i in range(len(aidx)):
            if stt[aidx[i][0]] == '음' or stt[aidx[i][0]] == '그' or stt[aidx[i][0]] == '어'or stt[aidx[i][0]] == '아':
                result['annotations'].append({'start': aidx[i][0], 'end': aidx[i][0] + 1, 'type': 'FILLER'})
            else :
                result['annotations'].append({'start': aidx[i][0], 'end': aidx[i][1] - 14, 'type': 'CANCELLATION'})

        p = [m.start(0) for m in re.finditer('\(pause\)', pause_final)]

        pidx = []
        for i in range(len(p)):
          tmp = p[i] - i*7
          pidx.append(tmp)

        for i in range(len(pidx)):  # pause, delay 구분 없이 pause 로 통일
            result['annotations'].append({'start': pidx[i]-1, 'end': pidx[i], 'type': 'PAUSE', 'duration': pause_idx[i]})

        if stt.endswith("\n"):
            stt = stt[:-1]
        result['textFile']=stt

        return result

    
    def stt_json(self, myaudio):
        sound, startidx, endidx, silenceidx = self.indexing(myaudio)
        pause_final, stt_t, pause_result, delay_result, pause_idx, start_idx, end_idx = self.do_stt(
            sound, myaudio, startidx, endidx, silenceidx)

        stt_t = stt_t.replace('\n', '') #stt_t
        stt = self.process_stt_result(stt_t)

        result = {'textFile': '', 'timestamps': [], 'annotations': []}
        for i in range(len(start_idx)):
            result['timestamps'].append({'start': start_idx[i], 'end': end_idx[i]})

        result = self.basic_annotation_stt(result,stt,pause_final,pause_idx)

        result['textFile'] = stt_t

        return result

    
    def parse_data(self, stt_result,stt_feedback):
        cnt=1
        text=""
        denotations="["
        attributes="["
        text=text+stt_result['textFile']+"\n"
        for j in range(len(stt_feedback)):
            denotations +='{ "id": "T'+str(cnt)+'", "span": { "begin": '+str(stt_feedback[j]['start'])+', "end": '+str(stt_feedback[j]['end'])+' }, "obj": "'+str(stt_feedback[j]['type'])+'" },'
            attributes +='{ "id": "A'+str(cnt)+'", "subj": "T'+str(cnt)+'", "pred": "Unsure", "obj": True },'
            cnt+=1
        denotations=denotations[:-1]
        attributes=attributes[:-1]
        denotations+="]"
        attributes+="]"
        return text,denotations,attributes

    
    def make_json(self, text,denotations,attributes):
        data = {
            "text": text,
            "denotations": ast.literal_eval(denotations) if type(denotations) == str else denotations ,
            "attributes": ast.literal_eval(attributes) if type(attributes) == str else attributes,
            "config": {
                "boundarydetection": False,
                "non-edge characters": [],
                "function availability": {
                    "logo" : False,
                    "relation": False,
                    "block": False,
                    "simple": False,
                    "replicate": False,
                    "replicate-auto": False,
                    "setting": False,
                    "read": False,
                    "write": False,
                    "write-auto": False,
                    "line-height": False,
                    "line-height-auto": False,
                    "help": False
                },
                "entity types": [
                    {
                        "id": "Cancellation",
                        "color": "#ff5050"
                    },
                    {
                        "id": "Filler",
                        "color": "#ffff50",
                        "default": True
                    },
                    {
                        "id": "Pause",
                        "color": "#404040"
                    }
                ],
                "attribute types": [
                    {
                        "pred": "Unsure",
                        "value type": "flag",
                        "default": True,
                        "label": "?",
                        "color": "#fa94c0"
                    },
                    {
                        "pred": "Note",
                        "value type": "string",
                        "default": "",
                        "values": []
                    }
                ]
            }
        }


    # 마지막 실행 함수
    def last_output(self, filename):
        filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.mp3" #파일형태 변경
        myaudio = AudioSegment.from_file(filepath)
        stt_result = self.stt_json(myaudio)
        stt_feedback = stt_result['annotations']
        text,denotations,attributes = self.parse_data(stt_result,stt_feedback)
        data = self.make_json(text,denotations,attributes)

        return json.dumps(data, indent=4,ensure_ascii=False)


    #한국어버전 끝
