# -*- coding: utf-8 -*-

import json
import requests
import os
import openai
from dotenv import load_dotenv
import re
import ast

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class JpStt:

    def do_stt(filename):
        res = JpStt.req_upload(file=filename, completion="sync")
        dic = json.loads(res.text)

        pause_threshold = 1000  # in milliseconds
        text = ""
        prev_word_end = 0

        for segment in dic["segments"]:
            for i, (word_start, word_end, word) in enumerate(segment["words"]):
                # Add pause duration if applicable
                if text != "" and word_start - prev_word_end > pause_threshold:
                    # text += f" ({word_start - prev_word_end} ms)"
                    text += f" (pause)"

                text += word
                prev_word_end = word_end

        prompt_message = (
            "Please annotate hesitating expressions such as 'え', 'あの', or 'えと' by marking them with '<...>(filler)'. "
            "For instance, convert 'え' to '<え>(filler)'"
            "When you encounter repeated expressions, mark the first occurrence with '-...-(cancellation)'."
            "For example, if '考える考えると' appears, it should be converted to '-考える-(cancellation)考えると'. Another example is -少なく-(cancellation)とも (pause)少なくて  "
            "If there are no such expressions, return the original sentence. \n\n" + text
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_message}],
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        print(response.choices[0].message.content)
        # Extract annotations directly here
        annotated_text = response.choices[0].message.content

        # Extract annotations (pauses, fillers, cancellations) from the annotated_text
        annotations = []

        # Regular expressions for pauses, fillers, and cancellations
        pause_pattern = re.compile(r"\\((\\d+) ms\\)")
        filler_pattern = re.compile(r"<(.*?)>\(filler\)")
        cancellation_pattern = re.compile(r"-([^-\[]*?)-\(cancellation\)")

        # Extract pauses
        for match in pause_pattern.finditer(annotated_text):
            annotations.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "type": "Pause",
                    "value": match.group(1),
                }
            )

        # Extract and adjust fillers
        for match in filler_pattern.finditer(annotated_text):
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

        # Extract and adjust cancellations
        for match in cancellation_pattern.finditer(annotated_text):
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

        result = {"textFile": annotated_text, "timestamps": [], "annotations": annotations}

        text, denotations, attributes = JpStt.parse_data(
            [result], [annotations]
        ) 

        result["denotations"] = denotations
        result["attributes"] = attributes

        json_output = JpStt.make_json(text, denotations, attributes)

        result["json_output"] = json_output

        return result


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
        }

        return data