from distutils.command.upload import upload
from server.apis import assignment, lecture
from server.services.stt_service import mapping_sst_user
from ..model import Assignment_feedback, Attendee, SttJob, User, Lecture, Assignment,Prob_region,Assignment_check,Assignment_check_list,Stt,Feedback2
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
from pydub import AudioSegment, silence
from worker import do_stt_work
from datetime import datetime,timedelta

import json
import os
# import librosa
import uuid
import ast

def prob_list_student(lecture_no:int,user_no:int):
    attendee = Attendee.query.filter_by(user_no = user_no, lecture_no = lecture_no).first()
    assignments = Assignment.query.filter(Assignment.lecture_no == lecture_no).filter(Assignment.open_time <= datetime.utcnow()+timedelta(hours=9)).all()
    res = []
    for assignment in assignments:
        assignment_check = Assignment_check.query.filter_by(assignment_no = assignment.assignment_no, attendee_no = attendee.attendee_no).order_by(Assignment_check.check_no.desc()).first()
        res.append({'as_no': assignment.assignment_no, 'as_name': assignment.as_name, "limit_time": assignment.limit_time, "end_submission": assignment_check.end_submission if assignment_check != None else None, "professor_review" : assignment_check.professor_review if assignment_check != None else None})
    db.session.remove()
    return res

def prob_list_professor(lecture_no:int,user_no:int):
    assignments = Assignment.query.filter(Assignment.lecture_no == lecture_no).all()
    res = [{'as_no': assignment.assignment_no, 'as_name': assignment.as_name,"open_time":assignment.open_time , "limit_time": assignment.limit_time, "reaveal" : True if assignment.open_time <= datetime.utcnow()+timedelta(hours=9) else False} for assignment in assignments]
    db.session.remove()
    return res

#major_convert={"한일통역":"ja-JP","한일번역":"ja-JP","한중통역":"zh-CN","한중번역":"zh-CN","한영통역":"en-US","한영번역":"en-US","한불통역":"fr-FR","한불번역":"fr-FR"}#임시용
major_convert={"ko":"ko-KR","jp":"ja-JP","en":"en-US","cn":"zh-CN","fr":"fr-FR"}
def make_as(user_no,lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region=None,user_info=None,prob_translang_source="ko",prob_translang_destination="ko"):
    acc=Assignment(user_no=user_no,lecture_no=lecture_no,week=week,limit_time=limit_time,as_name=as_name,as_type=as_type,keyword=keyword,description=description,re_limit=re_limit,speed=speed,disclosure=disclosure,original_text=original_text,upload_url=upload_url,translang=prob_translang_source,dest_translang=prob_translang_destination)
    db.session.add(acc)
    db.session.commit()
    lecture_major=prob_translang_source
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
            print(lecture_major)
            split_url=split_wav_save(upload_url,int(reg_start),int(reg_end))
            mapping_sst_user(acc.assignment_no, split_url,user_info)
            task = do_stt_work.delay(filename=split_url,locale=major_convert['jp'])
            pr = Prob_region(assignment_no=acc.assignment_no,region_index=reg_index,start=reg_start,end=reg_end,upload_url=split_url, job_id=task.id)
            db.session.add(pr)
            db.session.commit
        
def split_wav_save(upload_url,start,end):
    uuid_str=str(uuid.uuid4())
    audio: AudioSegment = AudioSegment.from_file(upload_url)
    audio[start * 1000:end * 1000].export(f"{os.environ['UPLOAD_PATH']}/{uuid_str}.wav", format="wav")
    return uuid_str
    

def mod_as(lecture_no,as_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region="",user_info=None,prob_translang_source="ko",prob_translang_destination="ko"):
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
    if(prob_translang_source!="ko"):
        acc.translang=prob_translang_source
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
    if(prob_translang_destination!=""):
        acc.dest_translang=prob_translang_destination
    db.session.add(acc)
    db.session.commit
    if region==None:
        return
    Prob_region.query.filter_by(assignment_no=as_no).delete()
    db.session.commit

    lecture_major=prob_translang_source
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
        json_result=ast.literal_eval(acc.stt_result)
        original_text=json_result["textFile"]
        original_text=original_text.replace("<","&lt")
        tmp["textFile"]=original_text.replace(">","&gt")
        tmp["timestamps"]=json_result["timestamps"]
        tmp["annotations"]=json_result["annotations"]
        tmp["is_seq"]=acc.is_seq
        original_result.append(tmp)
    return original_result

def get_prob_wav_url(as_no,user_no,lecture_no):
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=lecture_no).first()
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
    
def  check_assignment(as_no,lecture_no,uuid,user_info,text=""):
    acc=Prob_region.query.filter_by(assignment_no=as_no).all()
    if(len(acc)!=len(uuid) and text==""):
        return
    attend=Attendee.query.filter_by(user_no=user_info["user_no"],lecture_no=lecture_no).first()
    submit_cnt=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).count()
    print(submit_cnt)
    if(submit_cnt==None):
        submit_cnt=0
    #acc=Assignment_check(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1,user_trans_result=text,submit_time=(datetime.now()+timedelta(hours=6)),submit_cnt=submit_cnt+1)
    if text != "":
        ae_text, ae_denotations, ae_attributes = parse_ae_json(text)
    else:
        ae_text, ae_denotations, ae_attributes = "", "", ""
    acc=Assignment_check(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1,ae_text = ae_text,ae_denotations = ae_denotations,ae_attributes=ae_attributes,submit_time=(datetime.now()+timedelta(hours=6)),submit_cnt=submit_cnt+1)
    db.session.add(acc)
    db.session.commit()
    acc_locale=Assignment.query.filter_by(assignment_no=as_no).first()
    locale=acc_locale.dest_translang
    if(text==""):
        for uu in uuid:
            acc2=Assignment_check_list(check_no=acc.check_no,acl_uuid=uu)
            db.session.add(acc2)
            db.session.commit()
            do_stt_work.delay(filename=uu,locale=major_convert[locale])

def assignment_detail(as_no:int, user_no:int):
    assignment = Assignment.query.filter_by(assignment_no = as_no).first()
    attendee = Attendee.query.filter_by(user_no = user_no, lecture_no = assignment.lecture_no).first()
    assignment_check = Assignment_check.query.filter_by(assignment_no = as_no, attendee_no = attendee.attendee_no).order_by(Assignment_check.check_no.desc()).first()
    res = {"keyword" : "(없음)" if assignment.keyword == "" else assignment.keyword, "detail" : assignment.description, "limit_time" : assignment.limit_time, "assign_count" : assignment.assign_count, "open_time" : assignment.open_time, "file_name":assignment.file_name, "file_path":assignment.file_path, "as_name":assignment.as_name}
    if(assignment_check != None):
        res["feedback"] = assignment_check.professor_review
        res["end_submission"] = assignment_check.end_submission
        res["my_count"] = assignment_check.submit_cnt
    else:
        res["feedback"] = False
        res["end_submission"] = False
        res["my_count"] = None
    if not assignment.keyword_open and attendee.permission == 3:
        res["keyword"] = "(비공개) " + res["keyword"]
    elif not assignment.keyword_open and attendee.permission != 3:
        res["keyword"] = "(비공개)"
    return res

def get_as_name(as_no):
    acc=Assignment.query.filter_by(assignment_no=as_no).first()
    return acc.as_name

def get_stt_result(uuid):
    stt_result_list=[]
    stt_feedback_list=[]
    tmp_idx = 0
    correction = 1
    for i in uuid:
        print("uiud",i)
        tmp={}
        stt_acc=Stt.query.filter_by(wav_file=i["uuid"]).first()
        acc=SttJob.query.filter_by(stt_no=stt_acc.stt_no).first()
        if acc==None:
            return None,None
        tmp["sound"]=acc.sound
        tmp["startidx"]=acc.startidx
        tmp["endidx"]=acc.endidx
        tmp["silenceidx"]=acc.silenceidx
        stt_result=acc.stt_result.replace("'",'"')
        # stt_result=acc.stt_result
        # stt_result=stt_result.replace("'",'"')
        json_result=json.loads(stt_result)
        tmp["textFile"]=json_result["textFile"].replace("<","&lt").replace(">","&gt")
        # print(len(tmp["textFile"]))
        tmp["timestamps"]=json_result["timestamps"]
        tmp["annotations"]=json_result["annotations"]
        ann=ast.literal_eval(str(tmp["annotations"]))
        # print(str(tmp["annotations"]))
        for i in range(len(ann)):
            ann[i]["start"]+=tmp_idx #인덱스 보정
            ann[i]["end"]+=tmp_idx
        tmp_idx += len(tmp["textFile"]) + correction
        stt_feedback_list.append(ann)
        tmp["is_seq"]=acc.is_seq
        stt_result_list.append(tmp)
        # print(stt_result_list)
        # print(stt_feedback_list)
    return stt_result_list,stt_feedback_list
    
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
    as_list_result["as_no"]=vars(acc)["assignment_no"]
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

def set_feedback(as_no,lecture_no,professor_review,feedback,user_no):
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    check.professor_review=professor_review
    db.session.add(check)
    db.session.commit()
    part=0
    if feedback!=None:
        json_reg=ast.literal_eval(feedback[0])
        part=json_reg["probIndex"]
    acc=Assignment_feedback.query.filter_by(check_no=check.check_no,part=part).all()
    for i in acc:
        db.session.delete(i)
        db.session.commit()
    if feedback!=None:
        for reg in feedback:
            json_reg=ast.literal_eval(reg)
            reg_text=json_reg["text"]
            reg_taglist=','.join(json_reg["tagList"])
            reg_comment=json_reg["comment"]
            start=json_reg["sOffset"]
            end=json_reg["eOffset"]
            part=json_reg["probIndex"]
            acc=Assignment_feedback(check_no=check.check_no,target_text=reg_text,text_type=reg_taglist,comment=reg_comment,start=start,end=end,part=part)
            db.session.add(acc)
            db.session.commit()

            
def get_feedback(as_no,lecture_no,user_no):
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    pro_review=check.professor_review
    #utr=check.user_trans_result 
    utr=make_json(check.text,check.denotations, check.attributes)
    if(pro_review==""):
        pro_review=None
    if(utr==""):
        utr=None
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
        tmp["tagList"]=tmp["tagList"].replace(",",'","')
        tmp["comment"]=i.comment.replace("<","&lt")
        tmp["comment"]=tmp["comment"].replace(">","&gt")
        tmp["start"]=i.start
        tmp["end"]=i.end
        tmp["probIndex"]=i.part
        feedback_list.append(tmp)
    return utr,pro_review,feedback_list
    
def get_prob_submit_list(as_no,lecture_no):
    submit_list=[]
    attend=Attendee.query.filter_by(lecture_no=lecture_no).all()
    for i in attend:
        tmp={}
        tmp["attendee_no"]=i.attendee_no
        tmp["user_no"]=i.user_no
        user=User.query.filter_by(user_no=i.user_no).first()
        if(user.permission!=1 and user.permission!=2):#조교권한 학생급으로 변경
            continue
        tmp["major"]=user.major
        tmp["email"]=user.email
        tmp["name"]=user.name
        check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=i.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
        if(check==None):
            tmp["check"]="No"
            tmp["submit_time"]="ㅤ"
        else:
            tmp["check"]="Yes"
            tmp["submit_time"]=check.submit_time
        submit_list.append(tmp)

    return submit_list

def make_json(text,denotations,attributes):
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
    
    return json.dumps(data, indent=4,ensure_ascii=False)


def make_json_url(text,denotations,attributes,check,flag):
    domain = os.getenv("DOMAIN", "https://edu-trans.ewha.ac.kr:8443")
    filetmp = uuid.uuid4()
    filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.json"
    data=make_json(text,denotations,attributes)
    if(flag):
        # check.user_trans_result=data
        check.ae_text = text
        check.ae_denotations = str(denotations)
        check.ae_attributes = str(attributes)
        db.session.add(check)
        db.session.commit
    with open(filepath, 'w') as file:
        file.write(data)
    url =  domain + "/" + filepath
    return url

def get_json_feedback(as_no,lecture_no,user_no):
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    if(check==None):
        return "error:nocheck",""
    pro_review=check.professor_review
    # utr=check.user_trans_result
    # utr = check.ae_text + check.ae_denotations + check.ae_attributes
    if(check.ae_text == "" and check.ae_denotations == "" and check.ae_attributes == ""):
        wav_url,uuid=get_prob_wav_url(as_no,user_no,lecture_no)
        stt_result,stt_feedback=get_stt_result(uuid)
        if(stt_result==None):
            return "error:stt",""
        text,denotations,attributes=parse_data(stt_result,stt_feedback)
        denotations_json = json.loads(denotations)
        attributes_json = json.loads(attributes)
        url=make_json_url(text,denotations_json,attributes_json,check,1)
    else:
        # utr=make_json(check.ae_text, check.ae_denotations, check.ae_attributes)
        url=make_json_url(check.ae_text,check.ae_denotations, check.ae_attributes, check,0)
    return url, pro_review#json, 교수평가

def save_json_feedback(as_no,lecture_no,user_no,ae_attributes,ae_denotations,result,dlist,clist)->None:
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    if(result):
        check.professor_review=result
    if(ae_denotations):
        check.ae_denotations = ae_denotations
    if(ae_attributes):
       check.ae_attributes= ae_attributes
    db.session.add(check)
    db.session.commit()
    acc=Feedback2(attendee_no=attend.attendee_no,check_no=check.check_no,submission_count=check.submit_cnt,translation_error=clist[0],omission=clist[1],expression=clist[2],intonation=clist[3],grammar_error=clist[4],silence=dlist[0],filler=dlist[1],backtracking=dlist[2],others=dlist[3])
    db.session.add(acc)
    db.session.commit()

def parse_data(stt_result,stt_feedback):
    cnt=1
    text=""
    denotations="["
    attributes="["
    for i in range(len(stt_result)):
        text=text+stt_result[i]['textFile']+"\n"
        for j in range(len(stt_feedback[i])):
            denotations+='{ "id": "T'+str(cnt)+'", "span": { "begin": '+str(stt_feedback[i][j]['start'])+', "end": '+str(stt_feedback[i][j]['end'])+' }, "obj": "'+str(stt_feedback[i][j]['type'])+'" },'
            attributes+='{ "id": "A'+str(cnt)+'", "subj": "T'+str(cnt)+'", "pred": "Unsure", "obj": true },'
            cnt+=1
    denotations=denotations[:-1]
    attributes=attributes[:-1]
    denotations+="]"
    attributes+="]"
    return text,denotations,attributes

def parse_ae_json(ae_text:str):
    ae_json = json.loads(ae_text)
    text = ae_json["text"]
    denotations = ae_json["denotations"]
    attributes = ae_json["attributes"]
    return text, str(denotations), str(attributes)

def get_studentgraph(lecture_no,as_no,user_no):
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=lecture_no).first()
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.submit_cnt.asc())
    deliver_individual_list = []
    content_individual_list = []
    deliver_data_list = []
    content_data_list = []

    for row in check:
        feed=Feedback2.query.filter_by(attendee_no=attend.attendee_no,check_no=row.check_no)
        if(feed==None):
            return -1
        deliver_data=[feed.silence, feed.filler, feed.backtracking, feed.others] 
        content_data=[feed.translation_error, feed.omission, feed.expression, feed.intonation,feed.grammar_error]
        deliver_individual_list.append({
            "name": str(row.submit_cnt) + "회차",
            "data": deliver_data
        })
        deliver_data_list.append(deliver_data)
        content_individual_list.append({
            "name": str(row.submit_cnt) + "회차",
             "data": content_data
        })
        content_data_list.append(content_data)
    deliver_average = [sum(col) / len(col) for col in zip(*deliver_data_list)]
    content_average = [sum(col) / len(col) for col in zip(*content_data_list)]
    response={
        "DeliverIndividualList": deliver_individual_list,
        "DeliverAverage": deliver_average,
        "ContentIndividualList": content_individual_list,
        "ContentAverage": content_average
    }
    return response

def get_professorgraph(lecture_no,as_no,user_no):
    check=Assignment_check.query.filter_by(assignment_no=as_no,assignment_check=1)
    nam=[]
    for i in check:
        attend=Attendee.query.filter_by(attendee_no=i.attendee_no).first()
        user=User.query.filter_by(user_no=attend.user_no).first()
        nam.append({"name":user.name,"data": get_studentgraph(lecture_no,as_no,attend.user_no)})
    response={
        "result":nam
    }
    return response