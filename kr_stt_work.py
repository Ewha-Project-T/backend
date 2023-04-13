from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize

import os
import requests
import re
import fugashi
import json
import time
import uuid

class KorStt:
    def process_stt_result(self,stt):
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

    def basic_indexing(self,filename):
        filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.wav"
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

    def basic_do_stt(self,length,res, sound, startidx, endidx, silenceidx):
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
            stt = self.process_stt_result(recog["combinedRecognizedPhrases"][0]["lexical"])
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
        return tmp_text, pause_result, delay_result, pause_idx, startidx, endidx

    def basic_annotation_stt(self,result,stt,pause_idx):
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

    def request_api(self,length,myaudio,startidx,endidx):
        domain = os.getenv("DOMAIN", "https://edu-trans.ewha.ac.kr:8443")

        files = []
        local_file = []
        
        for i in range(length):
            filetmp = uuid.uuid4()
            filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
            myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
            files += [ domain + "/" + filepath ]
            local_file += [ filepath ]

        if not len(files) > 0:  
            return None  
        res={'values':[]}

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
        while len(res["values"]) == 0:
            res = requests.get(
                url,
                headers={ "Ocp-Apim-Subscription-Key": os.environ['STT_KEY'] }
            ).json()

            time.sleep(1)
        for file in local_file:
            os.unlink(file)          
        return res
    
    def execute(self,filename):
        result = {'textFile': '', 'timestamps': [], 'annotations': []}
        length,sound,startidx,endidx,silenceidx,myaudio=self.basic_indexing(filename)
        res=self.request_api(length,myaudio,startidx,endidx)
        if res==None:  
            raise Exception("INVALID-FILE")        

        for i in range(length):
            result['timestamps'].append({'start': startidx[i], 'end': endidx[i]})

        stt_text, pause_result, delay_result, pause_idx, startidx, endidx=self.basic_do_stt(length,res,sound,startidx,endidx,silenceidx)
        result=self.basic_annotation_stt(result,stt_text,pause_idx)
        return result,sound,startidx,endidx,silenceidx
    #한국어버전 끝

