from distutils.command.upload import upload
from server.apis import assignment, lecture
from server.services.stt_service import mapping_sst_user
from ..model import Assignment_feedback, Attendee, SttJob, User, Lecture, Assignment,Prob_region,Assignment_check,Assignment_check_list,Stt
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

#major_convert={"한일통역":"ja-JP","한일번역":"ja-JP","한중통역":"zh-CN","한중번역":"zh-CN","한영통역":"en-US","한영번역":"en-US","한불통역":"fr-FR","한불번역":"fr-FR"}#임시용
major_convert={"jp-ko":"ja-JP","en-ko":"en-US","cn-ko":"zh-CN"}
def make_as(lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region=None,user_info=None,prob_translang="ko-KR"):
    acc=Assignment(lecture_no=lecture_no,week=week,limit_time=limit_time,as_name=as_name,as_type=as_type,keyword=keyword,description=description,re_limit=re_limit,speed=speed,disclosure=disclosure,original_text=original_text,upload_url=upload_url,translang=prob_translang)
    db.session.add(acc)
    db.session.commit()
    print(prob_translang)
    lecture_major=prob_translang
    if(lecture_major in major_convert):
        lecture_major=major_convert[lecture_major]
    else:
        lecture_major="ko-KR"
    if region!=None:
        for reg in region:
            reg=reg.replace("'",'"')
            json_reg=json.loads(reg)
            reg_index=json_reg["index"]
            reg_start=json_reg["start"]
            reg_end=json_reg["end"]

            split_url=split_wav_save(upload_url,int(reg_start),int(reg_end))
            mapping_sst_user(acc.assignment_no, split_url,user_info)

            task = do_stt_work.delay(filename=split_url,locale=lecture_major)
            pr = Prob_region(assignment_no=acc.assignment_no,region_index=reg_index,start=reg_start,end=reg_end,upload_url=split_url, job_id=task.id)
            db.session.add(pr)
            db.session.commit
        
def split_wav_save(upload_url,start,end):
    uuid_str=str(uuid.uuid4())
    audio: AudioSegment = AudioSegment.from_file(upload_url)
    audio[start * 1000:end * 1000].export(f"{os.environ['UPLOAD_PATH']}/{uuid_str}.wav", format="wav")
    return uuid_str
    

def mod_as(lecture_no,as_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region="",user_info=None,prob_translang="ko-KR"):
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
    if(prob_translang):
        acc.translang=prob_translang
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

    lecture_major=prob_translang
    if(lecture_major in major_convert):
        lecture_major=major_convert[lecture_major]
    else:
        lecture_major="ko-KR"
    if region!=None:
        for reg in region:
            reg=reg.replace("'",'"')
            json_reg=json.loads(reg)
            reg_index=json_reg["index"]
            reg_start=json_reg["start"]
            reg_end=json_reg["end"]

            split_url=split_wav_save(upload_url,int(reg_start),int(reg_end))
            mapping_sst_user(acc.assignment_no, split_url,user_info)

            task = do_stt_work.delay(split_url,lecture_major)
            pr = Prob_region(assignment_no=acc.assignment_no,region_index=reg_index,start=reg_start,end=reg_end,upload_url=split_url, job_id=task.id)
            db.session.add(pr)
            db.session.commit()


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
def get_original_stt_result(prob_result):
    original_result=[]
    for i in prob_result:
        acc=SttJob.query.filter_by(job_id=i["job_id"]).order_by(SttJob.stt_no.desc()).first()
        if acc==None:
            return None
        tmp={}
        tmp["sound"]=acc.sound
        tmp["startidx"]=acc.startidx
        tmp["endidx"]=acc.endidx
        tmp["silenceidx"]=acc.silenceidx
        stt_result=acc.stt_result
        check_text=0
        stt_result=list(stt_result)
        for idx in range(len(stt_result)):
            if stt_result[idx]=='"' and check_text==0:
                check_text=1
            elif stt_result[idx]=='"' and check_text==1:
                check_text=0
            if check_text==0 and stt_result[idx]=="'":
                stt_result[idx]='"'       
        stt_result=''.join(stt_result)
        json_result=json.loads(stt_result)
        original_text=json_result["textFile"]
        original_text=original_text.replace("<","&lt")
        tmp["textFile"]=original_text.replace(">","&gt")
        tmp["timestamps"]=json_result["timestamps"]
        tmp["annotations"]=json_result["annotations"]
        tmp["is_seq"]=acc.is_seq
        original_result.append(tmp)
    return original_result

def get_prob_wav_url(as_no,user_info,lecture_no):
    attend=Attendee.query.filter_by(user_no=user_info["user_no"],lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    if(check==None):
        return None,None
    acc=Assignment_check_list.query.filter_by(check_no=check.check_no).all()
    stt_result=[]
    stt_uuid=[]
    for lec in acc:
        tmp={}
        tmp2={}
        tmp["wav_url"]=f"{os.environ['UPLOAD_PATH']}/{vars(lec)['acl_uuid']}.wav"
        tmp2["uuid"]=vars(lec)['acl_uuid']
        stt_result.append(tmp)
        stt_uuid.append(tmp2)
    return stt_result,stt_uuid

def delete_assignment(assignment_no):
    acc = Assignment.query.filter_by(assignment_no=assignment_no).first()
    db.session.delete(acc)
    db.session.commit
    
def check_assignment(as_no,lecture_no,uuid,user_info):
    acc=Prob_region.query.filter_by(assignment_no=as_no).all()
    if(len(acc)!=len(uuid)):
        return
    attend=Attendee.query.filter_by(user_no=user_info["user_no"],lecture_no=lecture_no).first()
    Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).delete()#check_list도 cascade되는지 확인
    acc=Assignment_check(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1)
    db.session.add(acc)
    db.session.commit()
    for uu in uuid:
        acc2=Assignment_check_list(check_no=acc.check_no,acl_uuid=uu)
        db.session.add(acc2)
        db.session.commit()
        do_stt_work.delay(uu)

def get_as_name(as_no):
    acc=Assignment.query.filter_by(assignment_no=as_no).first()
    return acc.as_name

def get_stt_result(uuid):
    stt_result_list=[]
    for i in uuid:
        tmp={}
        stt_acc=Stt.query.filter_by(wav_file=i["uuid"]).first()
        acc=SttJob.query.filter_by(stt_no=stt_acc.stt_no).first()
        if acc==None:
            return None
        tmp["sound"]=acc.sound
        tmp["startidx"]=acc.startidx
        tmp["endidx"]=acc.endidx
        tmp["silenceidx"]=acc.silenceidx
        stt_result=acc.stt_result
        stt_result=stt_result.replace("'",'"')
        json_result=json.loads(stt_result)
        original_text=json_result["textFile"]
        original_text=original_text.replace("<","&lt")
        tmp["textFile"]=original_text.replace(">","&gt")
        tmp["timestamps"]=json_result["timestamps"]
        tmp["annotations"]=json_result["annotations"]
        tmp["is_seq"]=acc.is_seq
        stt_result_list.append(tmp)
    return stt_result_list
    
def mod_assignment_listing(lecture_no,assignment_no):
    as_list_result={}
    acc= Assignment.query.filter_by(lecture_no=lecture_no,assignment_no=assignment_no).first()
    as_list_result["lecture_no"]=vars(acc)["lecture_no"]
    as_list_result["week"]=vars(acc)["week"]
    as_list_result["limit_time"]=vars(acc)["limit_time"]
    as_list_result["as_name"]=vars(acc)["as_name"]
    as_list_result["as_type"]=vars(acc)["as_type"]
    as_list_result["keyword"]=vars(acc)["keyword"]
    as_list_result["translang"]=vars(acc)["translang"]
    as_list_result["description"]=vars(acc)["description"]
    as_list_result["re_limit"]=vars(acc)["re_limit"]
    as_list_result["speed"]=vars(acc)["speed"]
    as_list_result["disclosure"]=vars(acc)["disclosure"]
    as_list_result["original_text"]=vars(acc)["original_text"]
    as_list_result["upload_url"]=vars(acc)["upload_url"]
    
    audio_list_result=[]
    audio_list=Prob_region.query.filter_by(assignment_no=assignment_no).all()
    for att in audio_list:
        tmp={}
        tmp["region_index"]=att.region_index
        tmp["start"]=att.start
        tmp["end"]=att.end
        tmp["upload_url"]=att.upload_url
        audio_list_result.append(tmp)

    return as_list_result,audio_list_result

def get_as_info(lecture_no,assignment_no):
    as_list_result={}
    acc= Assignment.query.filter_by(lecture_no=lecture_no,assignment_no=assignment_no).first()
    if acc==None:
        return None
    as_list_result["lecture_no"]=vars(acc)["lecture_no"]
    as_list_result["week"]=vars(acc)["week"]
    as_list_result["limit_time"]=vars(acc)["limit_time"]
    as_list_result["as_name"]=vars(acc)["as_name"]
    as_list_result["as_type"]=vars(acc)["as_type"]
    as_list_result["keyword"]=vars(acc)["keyword"]
    as_list_result["description"]=vars(acc)["description"]
    as_list_result["re_limit"]=vars(acc)["re_limit"]
    as_list_result["speed"]=vars(acc)["speed"]
    as_list_result["disclosure"]=vars(acc)["disclosure"]
    original_text=vars(acc)["original_text"]
    original_text=original_text.replace("<","&lt")
    as_list_result["original_text"]=original_text.replace(">","&gt")
    as_list_result["upload_url"]=vars(acc)["upload_url"]
    return as_list_result

def set_feedback(as_no,lecture_no,professor_review,feedback,user_info):
    attend=Attendee.query.filter_by(user_no=user_info["user_no"],lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    check.professor_review=professor_review
    db.session.add(check)
    db.session.commit()
    acc=Assignment_feedback.query.filter_by(check_no=check.check_no).all()
    for i in acc:
        db.session.delete(i)
        db.session.commit()
    if feedback!=None:
        for reg in feedback:
            json_reg=json.loads(reg)
            reg_text=json_reg["text"]
            reg_taglist=','.join(json_reg["tagList"])
            reg_comment=json_reg["comment"]
            acc=Assignment_feedback(check_no=check.check_no,target_text=reg_text,text_type=reg_taglist,comment=reg_comment)
            db.session.add(acc)
            db.session.commit()

            
def get_feedback(as_no,lecture_no,user_info):
    attend=Attendee.query.filter_by(user_no=user_info["user_no"],lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    pro_review=check.professor_review
    if(pro_review==""):
        pro_review=None
    acc=Assignment_feedback.query.filter_by(check_no=check.check_no).all()
    feedback_list=[]
    if(acc==None):
        feedback_list=None
    for i in acc:
        tmp={}
        tmp["text"]=i.target_text.replace("<","&lt")
        tmp["text"]=tmp["text"].replace(">","&gt")
        tmp["tagList"]=i.text_type.replace("<","&lt")
        tmp["tagList"]=tmp["tagList"].replace(">","&gt")
        tmp["tagList"]=tmp["tagList"].split(",")
        tmp["comment"]=i.comment.replace("<","&lt")
        tmp["comment"]=tmp["comment"].replace(">","&gt")
        feedback_list.append(tmp)
    return pro_review,feedback_list