import json
import os
import re
import uuid
from flask_jwt_extended import get_jwt_identity
import requests
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment, silence

from server import db
from ..model import Stt, SttJob
from worker import do_stt_work

def simultaneous_stt(filename):
    task = do_stt_work.delay(filename)
    return task.id

def stt_getJobResult(jobid):
    job = SttJob.query.filter_by(job_id=jobid).first()
    if job != None:
        return eval(job.stt_result)

    task = do_stt_work.AsyncResult(jobid)
    if not task.ready():
        return { 'state': task.state }

    res, sound, startidx, endidx, silenceidx = task.get()

    result = {'textFile': '', 'timestamps': [], 'annotations': []}
    for i in range(len(sound)):
        result['timestamps'].append({'start': startidx[i], 'end': endidx[i]})

    flag = True
    text = ''
    delay_result = 0
    pause_result = 0

    values = res["values"]
    for i in range(len(values)):
        kind = values[i]["kind"]
        if kind != "Transcription":
            continue

        recog = requests.get(values[i]["links"]["contentUrl"]).json()
        stt = process_stt_result(recog["recognizedPhrases"][0]["nBest"][0]["lexical"])
        text += stt
        sentences = sent_tokenize(stt)
        for sentence in sentences:
            # print(sentence)
            if sentence.endswith('.'):
                flag = True
            else:
                flag = False
        if i < len(sound) - 1:
            if flag == False:
                print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                text = text+'\n'
                pause_result += silenceidx[i]
            else:
                # 통역 개시 지연구간
                print("(delay: " + str(silenceidx[i]) + "sec)")
                text = text+'\n'
                delay_result += silenceidx[i]

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
                result['annotations'].append(
                    {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
            else:
                result['annotations'].append(
                    {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

        pidx = []
        indx = -1
        while True:
            indx = stt.find('\n', indx + 1)
            if indx == -1:
                break
            pidx.append(indx)
        for i in range(len(pidx)): # pause, delay 구분 없이 pause 로 통일
            result['annotations'].append({'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': silenceidx[i]})

        result['textFile'] += stt

    job = SttJob(
        job_id=task.id,
        sound=repr(sound),
        startidx=repr(startidx),
        endidx=repr(endidx),
        silenceidx=repr(silenceidx),
    )

    job.stt_result = repr(result)
    db.session.commit()

    return result


# def sequential_stt(filename, index):
#     myaudio = AudioSegment.from_file(
#         f'tmp/{filename}')  # 경로 변경 필요
#     result = {'textFile': '', 'timestamps': [], 'annotations': []}
#     silenceidxs = []
#     temp = []
#     for i in range(len(index)):
#         audio_part = myaudio[index[i][0]:index[i][1]]
#         sound, startidx, endidx, silenceidx = indexing(audio_part)
#         silenceidxs.append(silenceidx)
#         stt, pause_result, delay_result = do_stt(
#             sound, audio_part, startidx, endidx, silenceidx)

#         for j in range(len(sound)):
#             result['timestamps'].append(
#                 {'start': startidx[j]+index[i][0], 'end': endidx[j]+index[i][0]})

#         temp.append(stt)

#     text = '\n\n'.join(temp)
#     p = re.compile('(\w\(filler\)|\w+\s\w+\(backtracking\))')
#     fidx = []
#     while (True):
#         f = p.search(text)
#         if f == None:
#             break
#         fidx.append([f.start(), f.end()])
#         text = re.sub("(\(filler\)|\(backtracking\))", "", text, 1)

#     for i in range(len(fidx)):
#         if text[fidx[i][0]] == '음' or text[fidx[i][0]] == '그' or text[fidx[i][0]] == '어':
#             result['annotations'].append(
#                 {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
#         else:
#             result['annotations'].append(
#                 {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

#     idx = [m.start(0) + 1 for m in re.finditer('[^\\n]\\n[^\\n]', text)]
#     for i in range(len(idx)):  # pause, delay 구분 없이 pause 로 통일
#         result['annotations'].append(
#             {'start': idx[i], 'end': idx[i]+1, 'type': 'Pause', 'duration': silenceidxs[i]})

#     result['textFile'] = text

#     return result


def indexing(myaudio):
    print("detecting silence")
    dBFS = myaudio.dBFS
    sound = silence.detect_nonsilent(
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16)  # 1초 이상의 silence
    sound = [[(start), (stop)] for start, stop in sound]
    startidx = []
    endidx = []
    silenceidx = []
    print("indexing")
    for i in range(0, len(sound)):
        startidx.append(sound[i][0])
        endidx.append(sound[i][1] + 200)
        if i < len(sound) - 1:
            silenceidx.append(sound[i + 1][0] - sound[i][1])
    return sound, startidx, endidx, silenceidx


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

def do_stt(stt_id, sound, myaudio, startidx, endidx, silenceidx):
    domain = os.getenv("DOMAIN", "https://ewha.ltra.cc")

    files = []
    local_file = []
    for i in range(len(sound)):
        filetmp = uuid.uuid4()
        filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
        myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
        files += [ domain + "/" + filepath ]
        local_file += [ filepath ]
    
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

    result_link = webhook_res["links"]["files"]
    jobid = str(uuid.uuid4())
    # print(stt_id)
    # stt = Stt.query.filter_by(wav_file=stt_id).first()
    # if stt is None:
    #     return False

    job = SttJob(
        job_no=jobid,
        # stt_no=stt.stt_no,
        url=result_link,
        sound=repr(sound),
        startidx=repr(startidx),
        endidx=repr(endidx),
        silenceidx=repr(silenceidx),
        files=repr(local_file)
    )
    db.session.add(job)
    db.session.commit()
    
    return jobid

def mapping_sst_user(assignment, file):
    userinfo = get_jwt_identity()
    stt = Stt(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file)
    db.session.add(stt)
    db.session.commit()

def is_stt_userfile(assignment, file) -> bool:
    userinfo = get_jwt_identity()
    stt = Stt.query.filter_by(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file).first()
    if stt is None:
        return False
    return True

def remove_userfile(assignment, file) -> bool:
    userinfo = get_jwt_identity()
    stt = Stt.query.filter_by(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file)
    if stt is None:
        return False
    try:
        os.unlink(f"{os.getenv['UPLOAD_PATH']}/{file}")
    except:
        pass
    stt.delete()
    db.session.commit()
    return True

def get_userfile():
    userinfo = get_jwt_identity()
    stt = Stt.query.filter_by(user_no=userinfo["user_no"]).all()
    if stt is None:
        return False
    return stt

def get_sttjob(jobid):
    job = SttJob.query.filter_by(job_no=jobid).first()
    if job is None:
        return False
    return job

def get_stt_from_jobid(jobid):
    job = SttJob.query.filter_by(job_no=jobid).first()
    if job is None:
        return False
    
    stt = Stt.query.filter_by(stt_no=job.stt_no).first()
    if stt is None:
        return False
    return stt