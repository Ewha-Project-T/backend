#new_1122

from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize

import os
import requests
import re
import json
import time
import uuid
import openai
import ast


class KorStt:
    def process_stt_result(self,stt):
        result = stt
        client = openai.OpenAI(
            api_key="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",
        )

        response = client.chat.completions.create(
            model="gpt-4", messages=[{"role": "user", "content": "Mark '<f>' on the before hesitating expressions and mark '</f>' after hesitating expressions such as '음', '아', or '그' (example: <f>음</f>). And mark '<c>' before repeating expressions that can be removed and mark '</c>' after  repeating expressions that can be removed, such as '다릅' in '다릅 틀립니다.', '있었' in '있었 있었습니다'. (example: <c>다릅</c> 틀립니다.). At this time, maintain spacing. (example input:차장님. 어 / example output:차장님. <f>어</f>). However if there is no space, do not make space./n" + result}]
        )

        result = response.choices[0].message.content
        return result


    def basic_indexing(self,filename):
        filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.mp3"
        myaudio = AudioSegment.from_file(filepath)
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
        return length, sound, startidx, endidx, silenceidx, myaudio


    def basic_do_stt(self, res, sound, myaudio, startidx, endidx, silenceidx):
        text = ''
        delay_result = 0
        pause_result = 0
        pause_idx = []
        start_idx = []
        end_idx = []
        pause_final = ''

        i = -1

        for dic in res:
            i += 1
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
                    pause_final += "(pause)"
                    text = text+' '
                    pause_result += silenceidx[i]
                    pause_idx.append(silenceidx[i])
            
        return pause_final, text, pause_result, pause_idx, start_idx, end_idx

    def basic_annotation_stt(self, result, stt, pause_final, pause_idx):
        a = re.compile('(\<f\>.*?\<\/f\>|\<c\>.*?\<\/c\>)')
        fidx = []
        cidx = []

        while (True):
            f = a.search(stt)
            if f == None:
                break
            if f.group(1)[:3] == '<f>':
                stt = re.sub("(\<f\>)", "", stt, 1)
                stt = re.sub("(\<\/f\>)", "", stt, 1)
                fidx.append([f.start(), f.end()])
                
            elif f.group(1)[:3] == '<c>':
                stt = re.sub("(\<c\>)", "", stt, 1)
                stt = re.sub("(\<\/c\>)", "", stt, 1)
                cidx.append([f.start(), f.end()])

        for i in range(len(fidx)):
            result['annotations'].append({'start': fidx[i][0], 'end': fidx[i][1] - 7, 'type': 'FILLER'})

        for i in range(len(cidx)):
            result['annotations'].append({'start': cidx[i][0], 'end': cidx[i][1] - 7, 'type': 'CANCELLATION'})


        p = [m.start(0) for m in re.finditer('\(pause\)', pause_final)]

        pidx = []
        for i in range(len(p)):
            tmp = p[i] - i*7
            pidx.append(tmp)

        for i in range(len(pidx)):  # pause, delay 구분 없이 pause 로 통일
            if pidx[i] == 0:
                continue
            result['annotations'].append({'start': pidx[i]-1, 'end': pidx[i], 'type': 'PAUSE', 'duration': pause_idx[i]})

        if stt.endswith("\n"):
            stt = stt[:-1]
        result['textFile']=stt

        return result


    def request_api(self,length,myaudio,startidx,endidx):
        domain = os.getenv("DOMAIN", "https://edu-trans.ewha.ac.kr:8443")

        files = []
        local_file = []

        for i in range(length):
            filetmp = uuid.uuid4()
            filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
            myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
            files += [ domain + "/" + filepath ]
            local_file += [filepath]

        if not len(files) > 0:
            return None

        res=[0 for i in range(length)]
        
        k = -1
        for f in local_file:
            k += 1
            with open(f, 'rb') as payload:
                url = "https://koreacentral.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=ko-KR"
                headers = {
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": os.environ["STT_KEY"]
                }
                
                response = requests.request("POST", url, headers=headers, data=payload)
              
                if response.status_code != 200:
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
                res[k] = json.loads(response.text)

        for f in local_file:
            os.unlink(f)

        return res

    def parse_data(self, stt_result,stt_feedback):
        cnt=1
        text=""
        denotations="["
        text=text+stt_result['textFile']+"\n"
        for j in range(len(stt_feedback)):
            denotations +='{ "id": "T'+str(cnt)+'", "span": { "begin": '+str(stt_feedback[j]['start'])+', "end": '+str(stt_feedback[j]['end'])+' }, "obj": "'+str(stt_feedback[j]['type'])+'" },'
            cnt+=1
        denotations=denotations[:-1]
        denotations+="]"
        return text, denotations


    def make_json(self, text, denotations):
        data = {
            "text": text,
            "denotations": ast.literal_eval(denotations) if type(denotations) == str else denotations
        }

        return data


    #마지막 실행 함수

    def execute(self,filename):
        result = {'textFile': '', 'timestamps': [], 'annotations': []}
        length, sound, startidx, endidx, silenceidx, myaudio = self.basic_indexing(filename)
        res=self.request_api(length,myaudio,startidx,endidx)
        if res==None:
            raise Exception("INVALID-FILE")

        pause_final, stt_t, pause_result, pause_idx, start_idx, end_idx = self.basic_do_stt(res, sound, myaudio, startidx, endidx, silenceidx)

        stt_t = stt_t.replace('\n', '') #stt_t
        stt = self.process_stt_result(stt_t)

        result = {'textFile': '', 'timestamps': [], 'annotations': []}
        for i in range(len(start_idx)):
            result['timestamps'].append({'start': start_idx[i], 'end': end_idx[i]})

        result = self.basic_annotation_stt(result,stt,pause_final,pause_idx)
        result['textFile'] = stt_t
        stt_feedback = result['annotations']
        text,denotations = self.parse_data(result,stt_feedback)
        data = self.make_json(text,denotations)

        return json.dumps(data, indent=4, ensure_ascii=False)

    #한국어버전 끝
