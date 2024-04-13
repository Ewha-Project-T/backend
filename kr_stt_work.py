# 0413 수정 -> 맨 앞 pause 제거

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
        result_list = []
        stt_len = len(result)

        ## 빈 파일 핸들링
        if stt_len == 0:
            res = ' '

        else:     
            if stt_len > 2000:
                for i in range(0, stt_len, 2000):
                    result_list.append(result[i:i + 2000])
            else:
                result_list.append(result)

            res = ''

            for i in range(len(result_list)):
                result_t = result_list[i]
                stt_flag = 0
                last_punc = ''
                start_blank = ''

                if result_t[0] == ' ':
                    start_blank = ' '
                    result_t = result_t[1:]

                if result_t[-1] == '.' or result_t[-1] == ',' or result_t[-1] == '?':
                    stt_flag = 1
                    last_punc = result_t[-1]
                elif result_t[-1] == ' ':
                    stt_flag = 2
                    result_t = result_t[:-1]

                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY")},
                    json = {"model": "gpt-4-1106-preview", "seed": 1230, "messages": [{"role": "user",
                                                        "content": """Filler is a word used when there is hesitation during speech, such as '음', '그', '어', or '아'.
                                                        Mark '<f>' before filler and mark '</f>' after filler. (example: <f>음</f>).
                                                        Cancellation refers to a word that was uttered first among words that were accidentally uttered repeatedly, such as '다릅' in '다릅 틀립니다.', '앞으로' in '앞으로 앞으로는'.
                                                        Mark '<c>' before cancellation and mark '</c>' after cancellation. (example: <c>다릅</c> 틀립니다.).
                                                        (pause) is not a filler or cancellation.
                                                        Except that marks, do not change, ommit, repeat or add words.
                                                        Keep spacing and punctuation the same as the input sentence. If there are no such expressions, return the original sentence. \n""" + result_t}]}

                )

                response_dict =  response.json()

                if response.status_code >= 500:
                    print("gpt - server error :", response.status_code)
                    print(response_dict['error'])
                elif response.status_code >= 400:
                    print("gpt - client error :", response.status_code)
                    print(response_dict['error'])

                res_t = response_dict['choices'][0]['message']['content']

                if i < len(result_list) - 1:
                    if stt_flag == 1:
                        res += start_blank + res_t + last_punc
                    elif stt_flag == 2:
                        res += start_blank + res_t + ' '
                    else:
                        res += start_blank + res_t
                else:
                    res += start_blank + res_t

        return res


    def basic_indexing(self,filename):
        filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.mp3"
        myaudio = AudioSegment.from_file(filepath)
        dBFS = myaudio.dBFS
        sound = silence.detect_nonsilent(
            myaudio, min_silence_len=1000, silence_thresh=dBFS - 16, seek_step=100)  # 1초 이상의 silence
        sound = [[(start), (stop)] for start, stop in sound]
        stt_num = [1 for i in range(len(sound))]

        flag = 0

        while (flag == 0):
            stt_long = []

            for i in range(len(sound)):
                if sound[i][1] - sound[i][0] > 59000:
                    stt_long.append(i)

            if len(stt_long) == 0:
              flag = 1

            for j in range(len(stt_long)):
                tmp = (sound[stt_long[j] + j][1] - sound[stt_long[j] + j][0]) / 2
                sound.insert(stt_long[j] + (j+1) , [sound[stt_long[j] + j][0] + tmp, sound[stt_long[j] + j][1]])
                sound[stt_long[j] + j][1] = sound[stt_long[j] + j][0] + tmp
                stt_num.insert(stt_long[j] + (j+1), 0)

        length = len(sound)

        startidx = []
        endidx = []
        silenceidx = []
        for i in range(0, len(sound)):
            startidx.append(sound[i][0])
            endidx.append(sound[i][1] + 200)
            if i < len(sound) - 1:
                silenceidx.append(sound[i + 1][0] - sound[i][1])
                
        return length, sound, startidx, endidx, silenceidx, myaudio, stt_num


    def basic_do_stt(self, res, sound, myaudio, startidx, endidx, silenceidx, stt_num):
        delay_result = 0
        pause_result = 0
        pause_idx = []
        start_idx = []
        end_idx = []
        pause_final = ''

        i = -1

        #if sound[0][0] > 1000:
        #    pause_final += "(pause)"
        #    pause_idx.append(startidx[0])

        for dic in res:
            i += 1
            if dic.get("RecognitionStatus") == "Success":
                stt = dic.get("DisplayText")
                if len(stt)>0:
                    start_idx.append(startidx[i])
                    end_idx.append(endidx[i])
                sentences = sent_tokenize(stt)
                for sentence in sentences:
                    pause_final += sentence
                    pause_final += ' '

                if ((i < len(sound) - 1) and (stt_num[i] == 1)):
                    pause_final += "(pause)"
                    pause_result += silenceidx[i]
                    pause_idx.append(silenceidx[i])
            
        return pause_final, pause_result, pause_idx, start_idx, end_idx

    def basic_annotation_stt(self, result, stt, pause_idx):
        stt_fc = re.sub('\(pause\)', '', stt)

        f_s = [m.start(0) for m in re.finditer('\<f\>', stt_fc)]
        f_e = [m.start(0) for m in re.finditer('\<\/f\>', stt_fc)]

        c_s = [m.start(0) for m in re.finditer('\<c\>', stt_fc)]
        c_e = [m.start(0) for m in re.finditer('\<\/c\>', stt_fc)]

        f_cnt = 0
        c_cnt = 0

        for i in range(len(f_s)+len(c_s)):
            target = f_s + c_s
            target.sort()
            if stt_fc[(target[i]+1)] == 'f':
                result['annotations'].append({'start': f_s[f_cnt] - i*7 + 1, 'end': f_e[f_cnt] -3 - i*7 + 1, 'type': 'FILLER'})
                f_cnt += 1

            else:
                result['annotations'].append({'start': c_s[c_cnt] - i*7 + 1, 'end': c_e[c_cnt] -3 - i*7 + 1, 'type': 'CANCELLATION'})
                c_cnt += 1

        stt_p = re.sub('\<f\>|\<c\>|\<\/f\>|\<\/c\>', '', stt)        

        p = [m.start(0) for m in re.finditer('\(pause\)', stt_p)]

        pidx = []
        for i in range(len(p)):
            tmp = p[i] - i*7
            pidx.append(tmp)

        for i in range(len(pidx)):
            result['annotations'].append({'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': pause_idx[i]})

        stt_fin = re.sub('\(pause\)', '', stt_p)   

        result['textFile']=stt_fin

        return result


    def request_api(self, length, myaudio, startidx, endidx):
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
                        print("stt - HTTP error: ", e)
                    except requests.exceptions.ConnectionError as e:
                        print("stt - Error connecting to server: ", e)
                    except requests.exceptions.Timeout as e:
                        print("stt - Timeout error: ", e)
                    except requests.exceptions.RequestException as e:
                        print("stt - Error: ", e)
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
        if len(stt_feedback)>0:
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
        length, sound, startidx, endidx, silenceidx, myaudio, stt_num = self.basic_indexing(filename)
        res=self.request_api(length, myaudio, startidx, endidx)
        if res==None: 
            raise Exception("INVALID-FILE")

        pause_final, pause_result, pause_idx, start_idx, end_idx = self.basic_do_stt(res, sound, myaudio, startidx, endidx, silenceidx, stt_num)

        stt = self.process_stt_result(pause_final)

        result = {'textFile': '', 'timestamps': [], 'annotations': []}
        for i in range(len(start_idx)):
            result['timestamps'].append({'start': start_idx[i], 'end': end_idx[i]})

        result = self.basic_annotation_stt(result,stt,pause_idx)
        stt_now = re.sub("\<f\>|\<c\>|\<\/f\>|\<\/c\>|\(pause\)", "", stt)
        
        result['textFile'] = " " + stt_now
        stt_feedback = result['annotations']
        text,denotations = self.parse_data(result,stt_feedback)
        data = self.make_json(text,denotations)

        return json.dumps(data, indent=4, ensure_ascii=False)

    #한국어버전 끝
