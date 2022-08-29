from distutils.command.upload import upload
from server.apis import assignment
from server.services.stt_service import mapping_sst_user
from ..model import Attendee, User, Lecture, Assignment,Prob_region,Assignment_check,Assignment_check_list
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
from pydub import AudioSegment, silence
from worker import do_stt_work

import json
import os
# import librosa
import uuid

def prob_listing(lecture_no):
    as_list=Assignment.query.filter_by(lecture_no=lecture_no).all()
    as_list_result=[]
    for lec in as_list:
        tmp={}
        tmp["assignment_no"]=vars(lec)["assignment_no"]
        tmp["week"]=vars(lec)["week"]
        tmp["limit_time"]=vars(lec)["limit_time"]
        tmp["as_name"]=vars(lec)["as_name"]
        tmp["as_type"]=vars(lec)["as_type"]
        tmp["keyword"]=vars(lec)["keyword"]
        tmp["description"]=vars(lec)["description"]
        tmp["re_limit"]=vars(lec)["re_limit"]
        tmp["speed"]=vars(lec)["speed"]
        tmp["disclosure"]=vars(lec)["disclosure"]
        tmp["original_text"]=vars(lec)["original_text"]
        tmp["upload_url"]=vars(lec)["upload_url"]
        as_list_result.append(tmp)
    return as_list_result

def make_as(lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region="",user_info=None):
    acc=Assignment(lecture_no=lecture_no,week=week,limit_time=limit_time,as_name=as_name,as_type=as_type,keyword=keyword,description=description,re_limit=re_limit,speed=speed,disclosure=disclosure,original_text=original_text,upload_url=upload_url)
    db.session.add(acc)
    db.session.commit()
    
    for reg in region:
        reg=reg.replace("'",'"')
        json_reg=json.loads(reg)
        reg_index=json_reg["index"]
        reg_start=json_reg["start"]
        reg_end=json_reg["end"]

        split_url=split_wav_save(upload_url,int(reg_start),int(reg_end))
        mapping_sst_user(acc.assignment_no, split_url,user_info)

        task = do_stt_work.delay(split_url)
        pr = Prob_region(assignment_no=acc.assignment_no,region_index=reg_index,start=reg_start,end=reg_end,upload_url=split_url, job_id=task.id)
        db.session.add(pr)
        db.session.commit
        
def split_wav_save(upload_url,start,end):
    uuid_str=str(uuid.uuid4())
    audio: AudioSegment = AudioSegment.from_file(upload_url)
    audio[start * 1000:end * 1000].export(f"{os.environ['UPLOAD_PATH']}/{uuid_str}.wav", format="wav")
    return uuid_str
    

def mod_as(lecture_no,as_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region=""):
    acc=Assignment.query.filter_by(assignment_no=as_no).first()
    if(lecture_no!=""):
        acc.lecture_no=lecture_no
    if(week!=""):
        acc.week=week
    if(limit_time!=""):
        acc.limit_time=limit_time
    if(as_name!=""):
        acc.as_name=as_name
    if(as_type!=""):
        acc.as_type=as_type
    if(keyword!=""):
        acc.keyword=keyword
    if(description!=""):
        acc.description=description
    if(re_limit!=""):
        acc.relimit=re_limit
    if(speed!=""):
        acc.speed=speed
    if(disclosure!=""):
        acc.disclosure=disclosure
    if(original_text!=""):
        acc.original_text=original_text
    if(upload_url!=""):
        acc.upload_url=upload_url
    db.session.add(acc)
    db.session.commit
    if region==None:
        return
    Prob_region.query.filter_by(assignment_no=as_no).delete()
    db.session.commit

    for reg in region:
        reg=reg.replace("'",'"')
        json_reg=json.loads(reg)
        reg_index=json_reg["index"]
        reg_start=json_reg["start"]
        reg_end=json_reg["end"]

        split_url=split_wav_save(upload_url,int(reg_start),int(reg_end))
        mapping_sst_user(acc.assignment_no, split_url)

        task = do_stt_work.delay(split_url)
        pr = Prob_region(assignment_no=acc.assignment_no,region_index=reg_index,start=reg_start,end=reg_end,upload_url=split_url, job_id=task.id)
        db.session.add(pr)
        db.session.commit

        # pr=Prob_region(assignment_no=as_no,region_index=reg_index,start=reg_start,end=reg_end)
        # db.session.add(pr)
        # db.session.commit


def get_wav_url(as_no):
    acc=Prob_region.query.filter_by(assignment_no=as_no).all()
    prob_result=[]
    for lec in acc:
        tmp={}
        tmp["region_index"]=vars(lec)["region_index"]
        tmp["start"]=vars(lec)["start"]
        tmp["end"]=vars(lec)["end"]
        tmp["upload_url"]=f"{os.environ['UPLOAD_PATH']}/{vars(lec)['upload_url']}.wav"
        tmp["job_id"]=vars(lec)["job_id"]
        prob_result.append(tmp)
    return prob_result

def delete_assignment(assignment_no):
    acc = Assignment.query.filter_by(assignment_no=assignment_no).first()
    db.session.delete(acc)
    db.session.commit
    
def check_assignment(as_no,lecture_no,uuid,user_info):
    attend=Attendee.query.filter_by(user_no=user_info["user_no"],lecture_no=lecture_no).first()
    acc=Assignment_check(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1)
    db.session.add(acc)
    db.session.commit()
    for uu in uuid:
        acc2=Assignment_check_list(check_no=acc.check_no,acl_uuid=uu)
        db.session.add(acc2)
        db.session.commit()

def get_as_name(as_no):
    acc=Assignment.query.filter_by(assignment_no=as_no).first()
    return acc.as_name