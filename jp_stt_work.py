# -*- coding: utf-8 -*-

import json
import requests
import os
import openai
from dotenv import load_dotenv
import re

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def make_json(text, denotations, attributes):
    data = {
        "text": text,
        "denotations": denotations,
        "attributes": attributes,
        "config": {
            "boundarydetection": False,
            "non-edge characters": [],
            "function availability": {
                "logo": False,
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
                "help": False,
            },
            "entity types": [
                {"id": "Cancellation", "color": "#ff5050"},
                {"id": "Filler", "color": "#ffff50", "default": True},
                {"id": "Pause", "color": "#404040"},
            ],
            "attribute types": [
                {
                    "pred": "Unsure",
                    "value type": "flag",
                    "default": True,
                    "label": "?",
                    "color": "#fa94c0",
                },
                {"pred": "Note", "value type": "string", "default": "", "values": []},
            ],
        },
    }

    # Save the JSON to a file
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return data


def parse_data(stt_result, stt_feedback):
    cnt = 1
    text = ""
    denotations = []
    attributes = []

    for i in range(len(stt_result)):
        text += stt_result[i]["textFile"] + "\n"

        # Check if current stt_feedback[i] is a list and contains the expected data
        if not isinstance(stt_feedback[i], list):
            print(f"Error: stt_feedback[{i}] is not a list.")
            continue

        for j in range(len(stt_feedback[i])):
            # Check if current stt_feedback[i][j] is a dictionary and has the keys "start", "end", and "type"
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


def simultaneous_stt(filename):
    res = req_upload(file=filename, completion="sync")
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

    # print(text)
    # More explicit prompting for GPT model
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
        word_start = match.start(1)  # Start of the word inside angle brackets
        word_end = match.end(1)  # End of the word inside angle brackets
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
        word_start = match.start(1)  # Start of the word inside dashes
        word_end = match.end(1)  # End of the word inside dashes
        annotations.append(
            {
                "start": word_start,
                "end": word_end,
                "type": "Cancellation",
                "value": match.group(1),
            }
        )

    # Create the result dictionary to store the transcribed and annotated text and annotations
    result = {"textFile": annotated_text, "timestamps": [], "annotations": annotations}

    # Calling parse_data function
    text, denotations, attributes = parse_data(
        [result], [annotations]
    )  # wrapped annotations in a list to match expected structure

    result["denotations"] = denotations
    result["attributes"] = attributes

    json_output = make_json(text, denotations, attributes)

    # Appending the JSON output to the result dictionary
    result["json_output"] = json_output
    print("JSON saved to output.json")

    return result


def req_upload(file, completion, fullText=True):
    invoke_url = "https://clovaspeech-gw.ncloud.com/external/v1/4257/c2761d7a201319106f45d6557ef2a076e6285af96da7e4da3fce4c910a2e7174"

    request_body = {
        "language": "ja",
        "completion": completion,
        "fullText": fullText,
        "noiseFiltering": False,
    }
    headers = {
        "Accept": "application/json;UTF-8",
        "X-CLOVASPEECH-API-KEY": "3edd2f729d7544d9b77f157fd6256ab9",
    }

    files = {
        "media": open(file, "rb"),
        "params": (
            None,
            json.dumps(request_body, ensure_ascii=False).encode("UTF-8"),
            "application/json",
        ),
    }

    response = requests.post(
        headers=headers, url=invoke_url + "/recognizer/upload", files=files
    )
    return response


if __name__ == "__main__":
    stt_result = simultaneous_stt("C:/Users/kken1/OneDrive/바탕 화면/Ewha/답지/한일음성샘플.wav")
