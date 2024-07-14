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
from worker import do_stt_work#, do_sequential_stt_work

def simultaneous_stt(filename, locale):
    task = do_stt_work.delay(filename, locale)
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
"""
def sequential_stt(filename, index, locale):
    task = do_sequential_stt_work.delay(filename, index, locale)
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
"""
def mapping_sst_user(assignment, file,userinfo):
    stt = Stt(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file)
    db.session.add(stt)
    db.session.commit()
    return stt.stt_no

def is_stt_userfile(assignment, file,userinfo) -> bool:
    stt = Stt.query.filter_by(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file, is_deleted=False).first()
    if stt is None:
        return False
    return True

def remove_userfile(assignment, file,userinfo) -> bool:
    stt = Stt.query.filter_by(user_no=userinfo["user_no"], assignment_no=assignment, wav_file=file,is_deleted=False)
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
    stt = Stt.query.filter_by(user_no=userinfo["user_no"],is_deleted=False).first()
    if stt is None:
        return False
    return stt
"""
def get_sttjob(jobid):
    job = SttJob.query.filter_by(job_no=jobid).first()
    if job is None:
        return False
    return job

def get_stt_from_jobid(jobid):
    job = SttJob.query.filter_by(job_no=jobid).first()
    if job is None:
        return False
    
    stt = Stt.query.filter_by(stt_no=job.stt_no,is_deleted=False).first()
    if stt is None:
        return False
    return stt
    """