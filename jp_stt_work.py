from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize

import os
import requests
import re
import fugashi
import json
import uuid

#일본어버전 시작
class JpStt:
    def process_stt_result(self,stt):
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
        return length, sound, startidx, endidx, silenceidx, myaudio

    # worker.py 로 이동 필요
    def req_upload(self,file, completion,fullText=True):

        invoke_url = os.environ['CLOVASPEECH_STT_URL']

        request_body = {
            'language': 'ja',
            'completion': completion,
            'fullText': fullText,
            'noiseFiltering' : False
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': os.environ['CLOVASPEECH_STT_KEY']
        }
    #     print(json.dumps(request_body, ensure_ascii=False).encode('UTF-8'))
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
        }
        response = requests.post(headers=headers, url=invoke_url + '/recognizer/upload', files=files)
        return response



    def basic_do_stt(self,length,res, sound, startidx, endidx, silenceidx):

        
        flag = True
        text = ''
        delay_result = 0
        pause_result = 0
        pause_idx = []
        start_idx = []
        end_idx = []
        for i in range(len(res)):
            dic = res[i]
            # print(dic)
            if dic.get("result") == "COMPLETED":
                # tmp = dic.get("segments")
                tagger = fugashi.Tagger()
                words= [word.surface for word in tagger(dic['text'])]
                stt = self.process_stt_result(words)
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
        return text, pause_result, delay_result, pause_idx, start_idx, end_idx

    def basic_annotation_stt(self,result,stt,pause_idx):
        p = re.compile('(\w+\(filler\)|\w+\s\w+\(backtracking\))')

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
            elif stt[fidx[i][0]:fidx[i][0]+2] == 'あの' or stt[fidx[i][0]:fidx[i][0]+2] == 'えと' or stt[fidx[i][0]:fidx[i][0]+2] == 'その':
                result['annotations'].append(
                    {'start': fidx[i][0], 'end': fidx[i][0] + 2, 'type': 'FILLER'})
            else:
                result['annotations'].append(
                    {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})
        pidx = [m.start(0) + 1 for m in re.finditer('[^\.^\n]\n', stt)]
        for i in range(len(pidx)):  # pause, delay 구분 없이 pause 로 통일
            result['annotations'].append(
                {'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': pause_idx[i]})

        if stt.endswith("\n"):
            stt = stt[:-1]
        result['textFile'] = stt
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
        
        res=[0 for i in range(length)]

        for i in range(len(local_file)):
                response=self.req_upload(file=local_file[i], completion='sync')
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
                res[i] = json.loads(response.text)

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
