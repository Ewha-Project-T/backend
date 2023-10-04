# -*- coding: utf-8 -*-
from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize
import json
import requests
import os
import openai
from dotenv import load_dotenv
import re
import ast
import uuid

load_dotenv()


#일본어버전 시작
class JpStt:
    def process_stt_result(self,stt):
        result = stt
        openai.api_key = os.getenv("OPENAI_API_KEY")

        prompt_message = (
            "Please annotate hesitating expressions such as 'え', 'あの', or 'えと' by marking them with '<...>(filler)'. "
            "For instance, convert 'え' to '<え>(filler)'"
            "When you encounter repeated expressions, mark the first occurrence with '-...-(cancellation)'."
            "For example, if '考える考えると' appears, it should be converted to '-考える-(cancellation)考えると'. Another example is -少なく-(cancellation)とも (pause)少なくて  "
            "If there are no such expressions, return the original sentence. \n\n" + result
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_message}],
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        return response.choices[0].message.content

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
                words = dic["text"]
                stt = self.process_stt_result(words)
                text = text + stt
                if len(stt)>0:
                    start_idx.append(startidx[i])
                    end_idx.append(endidx[i])
                sentences = sent_tokenize(stt)
                for sentence in sentences:
                    print(sentence.replace(" ", ""))
                    if sentence.endswith("."):
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
        # Annotation Logic
        annotations = []
        # Regular expressions for pauses, fillers, and cancellations
        pause_pattern = re.compile(r"\((\d+) ms\)")
        filler_pattern = re.compile(r"<(.*?)>\(filler\)")
        cancellation_pattern = re.compile(r"-([^-\[]*?)-\(cancellation\)")

        # Extract pauses
        for match in pause_pattern.finditer(stt):
            annotations.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "type": "Pause",
                    "value": match.group(1),
                }
            )

        # Extract fillers
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

        # Extract cancellations
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

        # Create the result dictionary
        result = {"textFile": stt, "annotations": annotations}

        text, denotations, attributes = self.parse_data([result], [annotations])

        result["denotations"] = denotations
        result["attributes"] = attributes
        json_output = self.make_json(text, denotations, attributes)

        result["json_output"] = json_output

        return json_output

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
            stt_feedback = result['annotations']
            text,denotations,attributes = self.parse_data(result,stt_feedback)
            data = self.make_json(text,denotations,attributes)
            return json.dumps(data, indent=4,ensure_ascii=False)
    
    def parse_data(self, stt_result, stt_feedback):
        cnt = 1
        text = ""
        denotations = []
        attributes = []

        for i in range(len(stt_result)):
            text += stt_result[i]["textFile"] + "\n"

            if not isinstance(stt_feedback[i], list):
                print(f"Error: stt_feedback[{i}] is not a list.")
                continue

            for j in range(len(stt_feedback[i])):
                if not isinstance(stt_feedback[i][j], dict):
                    print(f"Error: stt_feedback[{i}][{j}] is not a dictionary.")
                    continue

                if not all(key in stt_feedback[i][j] for key in ["start", "end", "type"]):
                    print(
                        f"Error: stt_feedback[{i}][{j}] does not have all the required keys ('start', 'end', 'type')."
                    )
                    continue

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

        return text, denotations, attributes
    
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
        
        return data