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
from worker import do_stt_work, do_sequential_stt_work

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
    
    result = task.get()
    return result

def sequential_stt(filename, index):
    task = do_sequential_stt_work.delay(filename, index)
    return task.id

def seqstt_getJobResult(jobid):
    job = SttJob.query.filter_by(job_id=jobid).first()
    if job != None:
        return eval(job.stt_result)
    
    task = do_sequential_stt_work.AsyncResult(jobid)
    if not task.ready():
        return { 'state': task.state }
    
    result = task.get()
    return result

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

    stt = Stt.query.filter_by(wav_file=stt_id).first()
    if not stt:
        return False

    job = SttJob(
        job_no=jobid,
        stt_no=stt.stt_no,
        sound=repr(sound),
        startidx=repr(startidx),
        endidx=repr(endidx),
        silenceidx=repr(silenceidx),
        files=repr(local_file)
    )
    db.session.add(job)
    db.session.commit()
    
    return jobid

def mapping_sst_user(assignment, file,userinfo):
    # userinfo = get_jwt_identity()
    #userinfo = {"user_no":1}
    stt = Stt(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file)
    db.session.add(stt)
    db.session.commit()

def is_stt_userfile(assignment, file,userinfo) -> bool:
    # userinfo = get_jwt_identity()
    #userinfo = {"user_no":1}
    stt = Stt.query.filter_by(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file).first()
    if stt is None:
        return False
    return True

def remove_userfile(assignment, file,userinfo) -> bool:
    # userinfo = get_jwt_identity()
    #userinfo = {"user_no":1}
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

def get_userfile(userinfo):
    #userinfo = get_jwt_identity()
    #userinfo = {"user_no":1}
    stt = Stt.query.filter_by(user_no=userinfo["user_no"]).first()
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