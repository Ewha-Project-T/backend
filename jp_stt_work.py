# -*- coding: utf-8 -*-
from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize
import json
import requests
import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
import re
import ast
import uuid
client = OpenAI()

load_dotenv()


#일본어버전 시작
class JpStt:
    def process_stt_result(self,stt):
        result = stt
        openai.api_key = os.getenv("OPENAI_API_KEY")

        prompt_message = (
            "Please annotate hesitating expressions such as 'え', 'あの', or 'えと' by marking them with '<f>...</f>'. "
            "For instance, convert 'え' to '<f>え</f>'"
            "When you encounter repeated expressions, mark the first occurrence with '<c>...</c>'."
            "For example, if '考える考えると' appears, it should be converted to '<c>考える</c>考えると'. Another example is <c>少なく</c>とも少なくて  "
            "If there are no such expressions, return the original sentence. \n\n" + result
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_message}],
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
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

    def basic_do_stt(self,length,res, sound, startidx, endidx, silenceidx):
        # flag = True
        text = ""
        delay_result = 0
        pause_result = 0
        pause_idx = []
        start_idx = []
        end_idx = []
        for i in range(len(res)):
            dic = res[i]
            # print(dic)
            if dic.get("result") == "COMPLETED":
                words = dic["text"]
                stt = self.process_stt_result(words)
                text = text + stt
                if len(stt) > 0:
                    start_idx.append(startidx[i])
                    end_idx.append(endidx[i])
                sentences = sent_tokenize(stt)
                for sentence in sentences:
                    print(sentence.replace(" ", ""))
                if i < length - 1:
                    pause_duration = silenceidx[i]  # in milliseconds
                    print("(pause: " + str(silenceidx[i]) + "sec)") 
                    pause_placeholder = " "
                    text += pause_placeholder + "\n"
                    pause_result += pause_duration
                    pause_idx.append(pause_duration)

        return text, pause_result, delay_result, pause_idx, start_idx, end_idx
    
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
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
        }
        response = requests.post(headers=headers, url=invoke_url + '/recognizer/upload', files=files)
        return response

    def basic_annotation_stt(self,result,stt,pause_idx):

        annotations = []

        filler_pattern = re.compile(r"<f>(.*?)</f>")
        cancellation_pattern = re.compile(r"<c>(.*?)</c>")

        for i, char in enumerate(stt):
            if char == " " and i + 1 < len(stt) and stt[i + 1] == "\n":
                annotations.append(
                    {
                        "start": i,
                        "end": i + 1,
                        "type": "Pause",
                        "value": str(pause_idx.pop(0)) if pause_idx else "Unknown",
                    }
                )

        for match in filler_pattern.finditer(stt):
            word_start = match.start(1)
            word_end = match.end(1)
            annotations.append(
                {
                    "start": word_start,
                    "end": word_end,
                    "type": "Filler",
                    "value": match.group(1),
                }
            )


        for match in cancellation_pattern.finditer(stt):
            word_start = match.start(1)
            word_end = match.end(1)
            annotations.append(
                {
                    "start": word_start,
                    "end": word_end,
                    "type": "Cancellation",
                    "value": match.group(1),
                }
            )
        result['textFile']=stt

        return result, annotations

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
    
    def parse_data(self, stt_result,stt_feedback):
        cnt = 1
        text = ""
        denotations = []
        attributes = []

        for i in range(len(stt_result)):
            text += stt_result[i]["textFile"] + "\n"

            for j in range(len(stt_feedback[i])):
                denotation = {
                    "id": "T" + str(cnt),
                    "span": {
                        "begin": stt_feedback[i][j]["start"],
                        "end": stt_feedback[i][j]["end"],
                    },
                    "obj": stt_feedback[i][j]["type"],
                }
                denotations.append(denotation)

                attribute = {
                    "id": "A" + str(cnt),
                    "subj": "T" + str(cnt),
                    "pred": "Unsure",
                    "obj": True,
                }
                attributes.append(attribute)

                cnt += 1

        # Find all instances of filler and cancellation tags
        tag_positions = [(m.start(), m.end()) for m in re.finditer(r"</?f>|</?c>", text)]

        # Calculate the adjustment for each denotation index
        for denotation in denotations:
            adjustment = sum(end - start for start, end in tag_positions if start < denotation['span']['begin'])
            denotation['span']['begin'] -= adjustment
            denotation['span']['end'] -= adjustment

        # Update the text by removing the tags
        text = re.sub(r"</?f>|</?c>", "", text)
    
        return text, denotations, attributes
    
    def make_json(self, text,denotations,attributes):
        data = {
            "text": text,
            "denotations": ast.literal_eval(denotations) if type(denotations) == str else denotations ,
            "attributes": ast.literal_eval(attributes) if type(attributes) == str else attributes,
        }
        
        return data
    
    def execute(self,filename):
            result = {'textFile': '', 'timestamps': [], 'annotations': []}
            length,sound,startidx,endidx,silenceidx,myaudio=self.basic_indexing(filename)
            res=self.request_api(length,myaudio,startidx,endidx)
            if res==None:  
                raise Exception("INVALID-FILE")        
            for i in range(length):
                result['timestamps'].append({'start': startidx[i], 'end': endidx[i]})

            stt_text, pause_result, delay_result, pause_idx, startidx, endidx=self.basic_do_stt(length,res,sound,startidx,endidx,silenceidx)
            result, annotations=self.basic_annotation_stt(result,stt_text,pause_idx)
            text, denotations, attributes = self.parse_data([result], [annotations])
            result["denotations"] = denotations
            result["attributes"] = attributes
            data = self.make_json(text,denotations,attributes)

            return json.dumps(data, indent=4,ensure_ascii=False)