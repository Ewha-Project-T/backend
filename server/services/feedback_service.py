import ast
import json
import os
from urllib import parse
import zipfile
from server import db
from .assignment_service import get_prob_wav_url, get_stt_result, make_json, make_json_url, parse_data
from ..model import Assignment_check, Assignment_check_list, Attendee, Assignment, Assignment_management, Feedback2, Lecture, Prob_region, SelfStudy, Stt, SttJob, User
from sqlalchemy import func
from sqlalchemy.orm import aliased

def get_json_textae(as_no,user_no):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return "과제가 존재하지 않습니다.", False, False
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=assignment.lecture_no).first()
    if not attend:
        return "수강생이 아닙니다.", False, False
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no).order_by(Assignment_check.check_no.desc()).first()
    if not check:
        return "제출한 과제가 없습니다.", False, False
    assignment_management = Assignment_management.query.filter_by(assignment_no = as_no, attendee_no = attend.attendee_no).first()
    if assignment_management==None:
        return "학생 정보가 존재하지 않습니다.", False, False
    if assignment_management.end_submission is False:
        return "학생이 최종 제출하지 않았습니다.", False, False
    
    if assignment.as_type == "번역":
        text,denotations,attributes = check.user_trans_result,check.ae_denotations,check.ae_attributes
    elif(check.ae_text == "" and check.ae_denotations == "" and check.ae_attributes == ""):
        _,uuid=get_prob_wav_url(as_no,user_no,assignment.lecture_no)
        # stt_result,stt_feedback=get_stt_result(uuid)
        text,denotations,attributes = get_stt_result(uuid)
        if(text==None):
            return "STT 작업중 입니다.", False, False
        if(text==-1):
            return "STT 오류!!", False, False
        if(text==-2):
            return {"text": "STT 오류!!", "denotations": [], "attributes":[] ,"config":{"function availability": {
        "block": False, 
        "help": False, 
        "line-height-auto": False, 
        "logo": False, 
        "read": False, 
        "relation": False, 
        "replicate": False, 
        "replicate-auto": False, 
        "setting": False, 
        "simple": False, 
        "write": False, 
        "write-auto": False
      }}}, "A1", assignment_management.review
        check.ae_text,check.ae_denotations,check.ae_attributes=text,denotations,attributes
        db.session.commit()
        # text,denotations,attributes=parse_data(stt_result,stt_feedback)
        # url=make_json_url(text,denotations_json,attributes_json,check,1)
        # textae = make_json(text,denotations_json,attributes_json)
    else:
        # stt 넣기 용
        _,uuid=get_prob_wav_url(as_no,user_no,assignment.lecture_no)
        get_stt_result(uuid)
        print("assgin_check_no",check.check_no)
        # stt 넣기 끝
        text,denotations,attributes = check.ae_text,check.ae_denotations,check.ae_attributes
        # url=make_json_url(check.ae_text,check.ae_denotations, check.ae_attributes, check,0)
    if denotations != "None":
        denotations = str(sorted(ast.literal_eval(denotations), key=donotations_sort_key)) # sort by begin, end
    textae = make_json(text,denotations, attributes)
    textae = json.loads(textae)
    for attribute in textae["attributes"]:
        if type(attribute["obj"]) != bool:
            attribute["obj"] = parse.unquote(attribute["obj"])
    new_attribute = "A"+ str(find_max_attribute_number(ast.literal_eval(attributes))+1)
    return change_textae_denotations_to_korean(textae), new_attribute,assignment_management.review#json, 교수평가

def get_self_json_textae(as_no,user_no):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return "과제가 존재하지 않습니다.", False, False
    check=Assignment_check.query.filter_by(assignment_no=as_no).order_by(Assignment_check.check_no.desc()).first()
    if not check:
        return "제출한 과제가 없습니다.", False, False
    assignment_management = Assignment_management.query.filter_by(assignment_no = as_no).first()
    if assignment_management==None:
        return "학생 정보가 존재하지 않습니다.", False, False
    if assignment_management.end_submission is False:
        return "학생이 최종 제출하지 않았습니다.", False, False
    
    if assignment.as_type == "번역":
        text,denotations,attributes = check.user_trans_result,check.ae_denotations,check.ae_attributes
    elif(check.ae_text == "" and check.ae_denotations == "" and check.ae_attributes == ""):
        _,uuid=get_prob_wav_url(as_no,user_no,assignment.lecture_no, True)
        # stt_result,stt_feedback=get_stt_result(uuid)
        text,denotations,attributes = get_stt_result(uuid)
        if(text==None):
            return "STT 작업중 입니다.", False, False
        if(text==-1):
            return "STT 오류!!", False, False
        if(text==-2):
            return {"text": "STT 오류!!", "denotations": [], "attributes":[] ,"config":{"function availability": {
        "block": False, 
        "help": False, 
        "line-height-auto": False, 
        "logo": False, 
        "read": False, 
        "relation": False, 
        "replicate": False, 
        "replicate-auto": False, 
        "setting": False, 
        "simple": False, 
        "write": False, 
        "write-auto": False
      }}}, "A1", assignment_management.review
        check.ae_text,check.ae_denotations,check.ae_attributes=text,denotations,attributes
        db.session.commit()
        # text,denotations,attributes=parse_data(stt_result,stt_feedback)
        # url=make_json_url(text,denotations_json,attributes_json,check,1)
        # textae = make_json(text,denotations_json,attributes_json)
    else:
        # stt 넣기 용
        _,uuid=get_prob_wav_url(as_no,user_no,assignment.lecture_no, True)
        get_stt_result(uuid)
        print("assgin_check_no",check.check_no)
        # stt 넣기 끝
        text,denotations,attributes = check.ae_text,check.ae_denotations,check.ae_attributes
        # url=make_json_url(check.ae_text,check.ae_denotations, check.ae_attributes, check,0)
    if denotations != "None":
        denotations = str(sorted(ast.literal_eval(denotations), key=donotations_sort_key)) # sort by begin, end
    textae = make_json(text,denotations, attributes)
    textae = json.loads(textae)
    for attribute in textae["attributes"]:
        if type(attribute["obj"]) != bool:
            attribute["obj"] = parse.unquote(attribute["obj"])
    new_attribute = "A"+ str(find_max_attribute_number(ast.literal_eval(attributes))+1)
    return change_textae_denotations_to_korean(textae), new_attribute,assignment_management.review#json, 교수평가

def change_textae_denotations_to_korean(textae):
    # obj 값을 한글로 변환하는 맵핑
    obj_to_korean = {
        "expression": "표현",
        "translation_error": "오역",
        "grammar_error": "문법 오류",
        "pause": "침묵",
        "filler": "필러",
        "omission": "누락",
        "cancellation": "취소",
        "others": "기타"
    }

    for denotation in textae["denotations"]:
        try:
            denotation["obj"] = obj_to_korean[denotation["obj"].lower()]
        except:
            pass
    return textae

# attribute = [{'id': 'A1', 'subj': 'T1', 'pred': 'Unsure', 'obj': True}, {'id': 'A10', 'subj': 'T10', 'pred': 'Unsure', 'obj': True}, {'id': 'A11', 'subj': 'T11', 'pred': 'Unsure', 'obj': True}, {'id': 'A12', 'subj': 'T12', 'pred': 'Unsure', 'obj': True}, {'id': 'A13', 'subj': 'T13', 'pred': 'Unsure', 'obj': True}, {'id': 'A16', 'subj': 'T43', 'pred': 'Note', 'obj': 'asdfasdfasdfasdf'}, {'id': 'A2', 'subj': 'T2', 'pred': 'Unsure', 'obj': True}, {'id': 'A3', 'subj': 'T3', 'pred': 'Unsure', 'obj': True}, {'id': 'A4', 'subj': 'T4', 'pred': 'Unsure', 'obj': True}, {'id': 'A5', 'subj': 'T5', 'pred': 'Unsure', 'obj': True}, {'id': 'A6', 'subj': 'T6', 'pred': 'Unsure', 'obj': True}, {'id': 'A7', 'subj': 'T7', 'pred': 'Unsure', 'obj': True}, {'id': 'A8', 'subj': 'T8', 'pred': 'Unsure', 'obj': True}, {'id': 'A9', 'subj': 'T9', 'pred': 'Unsure', 'obj': True}]
def find_max_attribute_number(attributes):
    max_attribute = 0
    for attribute in attributes:
        if int(attribute['id'][1:]) > max_attribute:
            max_attribute = int(attribute['id'][1:])
    return max_attribute

def put_json_textae(as_no,user_no,ae_denotations,ae_attributes, is_self:bool = False):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return "과제가 존재하지 않습니다.", False
    if is_self:
        check=Assignment_check.query.filter_by(assignment_no=as_no).order_by(Assignment_check.check_no.desc()).first()
        assignment_management = Assignment_management.query.filter_by(assignment_no = as_no).first()
    else:
        attend=Attendee.query.filter_by(user_no=user_no,lecture_no=assignment.lecture_no).first()
        if not attend:
            return "수강생이 아닙니다.", False
        check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no).order_by(Assignment_check.check_no.desc()).first()
        assignment_management = Assignment_management.query.filter_by(assignment_no = as_no, attendee_no = attend.attendee_no).first()
    if not check:
        return "과제를 제출하지 않았습니다.", False
    if assignment_management==None:
        return "학생 정보가 존재하지 않습니다.", False
    if assignment_management.end_submission is False:
        return "학생이 최종 제출하지 않았습니다.", False

    if check.ae_text == "" and check.ae_denotations == "" and check.ae_attributes == "":
        return "수정 불가능 합니다.", False
    if ae_denotations != "None":
        if ae_denotations != "['Flag']":
            ae_denotations = str(sorted(ast.literal_eval(ae_denotations), key=donotations_sort_key)) # sort by begin, end
            check.ae_denotations = ae_denotations
    else:
        check.ae_denotations = "[]"
        check.ae_attributes = "[]"
    if ae_attributes != "None":
        if ae_attributes != "['Flag']":
            check.ae_attributes = ae_attributes#.replace("'",'&apos;')
    else:
            check.ae_attributes = "[]"
    
    db.session.commit()
    return "success", True

def donotations_sort_key(item):
    return (item['span']['begin'], item['span']['end'])

def get_feedback_info(as_no: int, student_no: int, user_no: int):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    user = User.query.filter_by(user_no=student_no).first()
    attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, user_no=student_no).first()
    if not attendee:
        return {"message": "해당 과제를 수강한 학생이 아닙니다.", "isSuccess": False}
    assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no, attendee_no = attendee.attendee_no).first()
    if assignment_manage.end_submission is False:
        return {"message": "아직 과제가 제출되지 않았습니다.", "isSuccess": False}
    assignment_check = Assignment_check.query.filter_by(assignment_no=as_no, attendee_no = attendee.attendee_no).order_by(Assignment_check.check_no.desc()).first()
    if not assignment_check:
        return {"message": "해당 과제를 제출한 학생이 아닙니다.", "isSuccess": False}
    if assignment.user_no != user_no:
        if assignment_manage.attendee_no != attendee.attendee_no or assignment_manage.review is False:
            return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    professor_no = assignment.user_no
    assignment_audio = Prob_region.query.filter_by(assignment_no=as_no).all()
    res = dict()
    res["as_type"] = assignment.as_type
    res["assignment_name"] = assignment.as_name
    res["dest_translang"] = assignment.dest_translang
    if assignment.as_type == "번역":
        res["student_name"] = user.name
        res["submit_time"] = assignment_manage.end_submission_time
        res["limit_time"] = assignment.limit_time
        res["original_text"] = assignment.original_text
        res["isSuccess"] = True
        return res

    if not assignment_audio:
        return {"message": "해당 과제의 오디오 파일이 존재하지 않습니다.", "isSuccess": False}
    assignment_check_list = Assignment_check_list.query.filter_by(check_no=assignment_check.check_no).all()
    if not assignment_check_list:
        return {"message": "해당 학생의 오디오 파일이 존재하지 않습니다.", "isSuccess": False}
    stt = Stt.query.filter_by(assignment_no=as_no, user_no = professor_no, is_deleted=False).all()
    text,denotations_json,attributes_json ="",[],[]
    res["student_delay"] = []
    for st in stt:
        stt_job = SttJob.query.filter_by(stt_no=st.stt_no).first()
        if stt_job is None:
            return {"message": "교수님의 음원 STT 작업 진행중입니다.", "isSuccess": False}
        if stt_job.stt_result is None:
            return {"message": "STT 작업 진행 중 입니다.", "isSuccess": False}
        try:
            result = json.loads(stt_job.stt_result)
            text += result["text"]
            origin_delay=stt_job.delay
        except:
            if len(stt_job.stt_result) > 1:
                text = stt_job.stt_result
                break
        res["student_delay"].append(stt_job.delay)
        # denotations_json += result["denotations"]
        # attributes_json += result["attributes"]

    origin_delay=0
    # res["original_ae"] = json.loads(make_json(text, denotations_json, attributes_json))
    res["original_tts"] = text
    res["original_text"] = assignment.original_text
    res["original_delay"] = origin_delay
    res["student_name"] = user.name
    res["submit_time"] = assignment_manage.end_submission_time
    res["limit_time"] = assignment.limit_time

    res["assignment_audio"] = [make_audio_format(assignment_audio) for assignment_audio in assignment_audio]
    res["student_audio"] = [make_audio_format(assignment_check_list, index) for index, assignment_check_list in enumerate(assignment_check_list)]
    # res["student_delay"] = [get_audio_delay(assignment_check_list, index) for index, assignment_check_list in enumerate(assignment_check_list)]
    res["isSuccess"] = True
    
    return res

def get_self_feedback_info(as_no: int, user_no: int):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if assignment.user_no != user_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no).first()
    if assignment_manage.end_submission is False:
        return {"message": "아직 과제가 제출되지 않았습니다.", "isSuccess": False}
    assignment_check = Assignment_check.query.filter_by(assignment_no=as_no).order_by(Assignment_check.check_no.desc()).first()
    if not assignment_check:
        return {"message": "해당 과제를 제출한 학생이 아닙니다.", "isSuccess": False}

    professor_no = assignment.user_no
    assignment_audio = Prob_region.query.filter_by(assignment_no=as_no).all()
    res = dict()
    res["as_type"] = assignment.as_type
    res["assignment_name"] = assignment.as_name
    res["dest_translang"] = assignment.dest_translang
    if assignment.as_type == "번역":
        res["student_name"] = "자습"
        res["submit_time"] = assignment_manage.end_submission_time
        res["limit_time"] = assignment.limit_time
        res["original_text"] = assignment.original_text
        res["isSuccess"] = True
        return res

    if not assignment_audio:
        return {"message": "해당 과제의 오디오 파일이 존재하지 않습니다.", "isSuccess": False}
    assignment_check_list = Assignment_check_list.query.filter_by(check_no=assignment_check.check_no).all()
    if not assignment_check_list:
        return {"message": "해당 학생의 오디오 파일이 존재하지 않습니다.", "isSuccess": False}
    stt = Stt.query.filter_by(assignment_no=as_no, user_no = professor_no, is_deleted=False).all()
    prob_region_count = Prob_region.query.filter_by(assignment_no=as_no).count()
    text,denotations_json,attributes_json ="",[],[]
    res["student_delay"] = []
    for st in stt[:prob_region_count]:
        stt_job = SttJob.query.filter_by(stt_no=st.stt_no).first()
        if stt_job is None:
            print(st.stt_no)
            return {"message": "교수님의 음원 STT 작업 진행중입니다.", "isSuccess": False}
        if stt_job.stt_result is None:
            return {"message": "STT 작업 진행 중 입니다.", "isSuccess": False}
        try:
            result = json.loads(stt_job.stt_result)
            text += result["text"]
            origin_delay=stt_job.delay
        except:
            if len(stt_job.stt_result) > 1:
                text = stt_job.stt_result
                break
        res["student_delay"].append(stt_job.delay)
        # denotations_json += result["denotations"]
        # attributes_json += result["attributes"]

    
    # res["original_ae"] = json.loads(make_json(text, denotations_json, attributes_json))
    res["original_tts"] = text
    res["original_text"] = assignment.original_text
    res["original_delay"] = origin_delay=origin_delay
    res["student_name"] = "자습"
    res["submit_time"] = assignment_manage.end_submission_time
    res["limit_time"] = assignment.limit_time

    res["assignment_audio"] = [make_audio_format(assignment_audio) for assignment_audio in assignment_audio]
    res["student_audio"] = [make_audio_format(assignment_check_list, index) for index, assignment_check_list in enumerate(assignment_check_list)]
    # res["student_delay"] = [get_audio_delay(assignment_check_list, index) for index, assignment_check_list in enumerate(assignment_check_list)]
    res["isSuccess"] = True
    
    return res

def make_audio_format(prob_region, id=0):
    url = prob_region.upload_url if hasattr(prob_region, "upload_url") else prob_region.acl_uuid
    return {
            "label": "원문 구간 " + str(prob_region.region_index)  if hasattr(prob_region, "region_index") else "학생 구간" + str(id + 1),
            # "label": int(prob_region.region_index) if hasattr(prob_region, "region_index") else id,
            "value": "./upload/" + url + ".mp3",
    }
def get_audio_delay(prob_region, id=0):
    url = prob_region.upload_url if hasattr(prob_region, "upload_url") else prob_region.acl_uuid
    stt= Stt.query.filter_by(wav_file=url, is_deleted=False).first()
    print(url)
    sttjob= SttJob.query.filter_by(stt_no=stt.stt_no).first()
    delay=0
    if sttjob!=None:
        delay=sttjob.delay
    return {
        "delay":delay
    }
def get_feedback_review(as_no:int, student_no:int,user_no:int, is_self:bool=False):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if is_self:
        self = SelfStudy.query.filter_by(assignment_no=as_no, user_no=user_no).first()
        if not self:
            print(as_no, user_no)
            return {"message": "해당 과제를 수강한 학생이 아닙니다.", "isSuccess": False}
        assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no).first()
    else:
        attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, user_no=student_no).first()
        if not attendee:
            return {"message": "해당 강의를 수강한 학생이 아닙니다.", "isSuccess": False}
        assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no, attendee_no = attendee.attendee_no).first()
    if assignment.user_no != user_no and assignment_manage.attendee_no != attendee.attendee_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    res = dict()
    res["review"] = assignment_manage.review
    return res

def save_feedback_review(as_no:int, student_no:int, user_no:int,review:str, is_self:bool=False):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if not assignment.user_no == user_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    if is_self:
        self = SelfStudy.query.filter_by(assignment_no=as_no, user_no=user_no).first()
        if not self:
            return {"message": "해당 과제를 수강한 학생이 아닙니다.", "isSuccess": False}
        assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no).first()
    else:
        attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, user_no=student_no).first()
        if not attendee:
            return {"message": "해당 강의를 수강한 학생이 아닙니다.", "isSuccess": False}
        assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no, attendee_no = attendee.attendee_no).first()
        save_feedback(assignment,attendee)
    assignment_manage.review = review
    db.session.commit()
    return {"message": "피드백이 저장되었습니다.", "isSuccess": True}

def update_graph(as_no:int, user_no:int, is_self:bool=False):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if is_self:
        attendee = user_no
    else:
        attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, user_no=user_no).first()
    if not attendee:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    save_feedback(assignment,attendee, is_self)
    db.session.commit()
    return

def update_open(as_no:int, user_no:int, open:bool):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if not assignment.user_no == user_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    assignment.open = open
    db.session.commit()
    return

def save_feedback(assignment:Assignment,attendee:Attendee, is_self:bool=False):
    if is_self:
        feedback = Feedback2.query.filter_by(assignment_no=assignment.assignment_no, lecture_no = 0).first()
    else:
        feedback = Feedback2.query.filter_by(assignment_no=assignment.assignment_no, attendee_no=attendee.attendee_no).first()
    if not feedback:
        if is_self:
            feedback = Feedback2(assignment_no=assignment.assignment_no, attendee_no=None, lecture_no = 0)
        else:
            feedback = Feedback2(assignment_no=assignment.assignment_no, attendee_no=attendee.attendee_no, lecture_no=assignment.lecture_no)
        db.session.add(feedback)
    if is_self:
        assignment_check = Assignment_check.query.filter_by(assignment_no=assignment.assignment_no).order_by(Assignment_check.check_no.desc()).first()
    else:
        assignment_check = Assignment_check.query.filter_by(assignment_no=assignment.assignment_no, attendee_no=attendee.attendee_no).order_by(Assignment_check.check_no.desc()).first()
    value = { "translation_error":0,"omission":0,"expression":0,"intonation":0,"grammar_error":0,"silence":0,"filler":0,"backtracking":0,"others":0}
    for denotation in ast.literal_eval(assignment_check.ae_denotations):
        objs = [obj.strip() for obj in denotation["obj"].lower().split(",")]
        for obj in objs:
            if obj=="pause":
                obj="silence"
            if obj == "canclellation":
                obj = "backtracking"
            if obj in value.keys():
                if obj=="pause":
                    value["silence"]+=1
                value[obj]+=1
            else:
                value["others"]+=1
    for key, val in value.items():
        setattr(feedback, key, val)
    return
def get_all_graphs(as_no:int, user_no:int):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    # if not assignment.user_no == user_no:
    #     return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    lecture = Lecture.query.filter_by(lecture_no=assignment.lecture_no).first()
    if not lecture:
        return {"message": "해당 강의가 존재하지 않습니다.", "isSuccess": False}
    attendees = Attendee.query.filter_by(lecture_no=lecture.lecture_no).all()[1:]
    res = {
        "Delivery" : avg_delivery(lecture.lecture_no, assignment.assignment_no),
        "Accuracy" : avg_accuracy(lecture.lecture_no, assignment.assignment_no),
        "DeliveryDetail" : detail_delivery(lecture.lecture_no, assignment.assignment_no),
        "AccuracyDetail" : detail_accuracy(lecture.lecture_no, assignment.assignment_no),
        "DeliveryAvg" : [
            {
                "name": attendee.user.name,
                "data":avg_delivery(lecture.lecture_no, assignment.assignment_no,1, attendee)
            } for attendee in attendees
        ],
        "AccuracyAvg" : [
            {
                "name": attendee.user.name,
                "data": avg_accuracy(lecture.lecture_no, assignment.assignment_no, 1, attendee)
            } for attendee in attendees
        ],
        "as_type": assignment.as_type,
        "isSuccess": True,
    }
    return res

def get_my_graphs(as_no, user_no, is_self:bool=False):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if is_self:
        attendee = user_no
    else:
        attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, user_no=user_no).first()
        if not attendee:
            return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    lecture = Lecture.query.filter_by(lecture_no=assignment.lecture_no).first()
    if not lecture:
        return {"message": "해당 강의가 존재하지 않습니다.", "isSuccess": False}
    res = {
    "DeliveryDetail": my_delivery(attendee, lecture.lecture_no, assignment.assignment_no, is_self),
    "AccuracyDetail": my_accuracy(attendee, lecture.lecture_no, assignment.assignment_no, is_self),
    "as_type": assignment.as_type,
    "isSuccess": True,
    }

    if not is_self:
        res["Delivery"] = avg_delivery(lecture.lecture_no, assignment.assignment_no, 1, attendee)
        res["Accuracy"] = avg_accuracy(lecture.lecture_no, assignment.assignment_no, 1, attendee)

    return res

def avg_delivery(lecture_no:int, assingment_no:int, flag:int = 0, me=None):
    attendees = Attendee.query.filter_by(lecture_no=lecture_no).all()[1:]
    res = []
    my_score = []
    avg = [0.0 for i in range(4)]
    for attendee in attendees:
        data = dict()
        data["name"] = attendee.user.name
        data["data"] = []
        for index, i in enumerate(["silence", "filler", "backtracking", "others"]):
            value = Feedback2.query.filter_by(
                lecture_no=lecture_no, 
                attendee_no=attendee.attendee_no
            ).filter(Feedback2.assignment_no == assingment_no
                     ).with_entities(func.avg(getattr(Feedback2, i))).scalar()
            
            # value가 None인지 확인하고, None인 경우 0.0으로 설정
            value = 0.0 if value is None else float(value)
            data["data"].append(float(value))
            avg[index] += float(value)
        res.append(data)
        if me:
            if me.attendee_no == attendee.attendee_no:
                my_score.append(data)
    if len(attendees) != 0:
        for i in range(4):
            avg[i] = round(avg[i] / len(attendees),2)
    if flag:
        my_score.append({"name": "평균", "data": avg})
        return my_score
    return res

def avg_accuracy(lecture_no:int, assingment_no:int, flag:int = 0, me=None):
    attendees = Attendee.query.filter_by(lecture_no=lecture_no).all()[1:]
    res = []
    my_score = []
    avg = [0.0 for i in range(6)]
    for attendee in attendees:
        data = dict()
        data["name"] = attendee.user.name
        data["data"] = []
        for index, i in enumerate(["translation_error", "omission", "expression", "intonation", "grammar_error", "others"]):
            value = Feedback2.query.filter_by(
                lecture_no=lecture_no, 
                attendee_no=attendee.attendee_no
            ).filter(Feedback2.assignment_no == assingment_no
                     ).with_entities(func.avg(getattr(Feedback2, i))).scalar()
            value = 0.0 if value is None else float(value)
            data["data"].append(float(value))
            avg[index] += float(value)
        res.append(data)
        if me:
            if me.attendee_no == attendee.attendee_no:
                my_score.append(data)
    if len(attendees) != 0:
        for i in range(6):
            avg[i] = round(avg[i] / len(attendees),2)
    if flag:
        my_score.append({"name": "평균", "data": avg})
        return my_score
    return res

def detail_delivery(lecture_no:int, assignment_no:int):
    attendees = Attendee.query.filter_by(lecture_no=lecture_no).all()[1:]
    assignments = Assignment.query.filter_by(lecture_no=lecture_no).filter(Assignment.assignment_no <= assignment_no).all()

    res = []
    for attendee in attendees:
        data = dict()
        data["name"] = attendee.user.name
        data["data"] = []
        for index, assignment in enumerate(assignments, start=1):  # start=1로 설정하여 1부터 시작
            tmp = dict()
            tmp["name"] = str(index) + "회차"
            tmp["data"] = []
            for i in ["silence", "filler", "backtracking", "others"]:
                value = Feedback2.query.filter_by(
                    lecture_no=lecture_no, 
                    attendee_no=attendee.attendee_no,
                    assignment_no=assignment.assignment_no
                ).with_entities(getattr(Feedback2, i)).scalar()
                value = 0.0 if value is None else float(value)
                tmp["data"].append(float(value))
            data["data"].append(tmp)
        data["data"] = data["data"][-3:]
        res.append(data)

    #뒤에서 3번째까지만 보여주기
    return res

def my_delivery(attendee, lecture_no, assignment_no, is_self:bool):
    assignments = Assignment.query.filter_by(lecture_no=lecture_no).filter(Assignment.assignment_no <= assignment_no).all()
    now_assignment = assignments[-1]
    res = []
    data = dict()
    if is_self:
        data["name"] = "자습"
    else:
        data["name"] = attendee.user.name
    data["data"] = []
    for index, assignment in enumerate(assignments, start=1):  # start=1로 설정하여 1부터 시작
        if is_self:
                if now_assignment.as_type != assignment.as_type:
                    continue
        tmp = dict()
        tmp["name"] = str(index) + "회차"
        tmp["data"] = []
        for i in ["silence", "filler", "backtracking", "others"]:
            query = Feedback2.query.filter_by(
                lecture_no=lecture_no, 
                assignment_no=assignment.assignment_no
            )
            if not is_self:
                query = query.filter_by(attendee_no=attendee.attendee_no)

            value = query.with_entities(getattr(Feedback2, i)).scalar()
            value = 0.0 if value is None else float(value)
            tmp["data"].append(float(value))
        data["data"].append(tmp)
    data["data"] = data["data"][-3:]
    res.append(data)

    #뒤에서 3번째까지만 보여주기
    return res

def my_accuracy(attendee, lecture_no, assignment_no, is_self:bool):
    assignments = Assignment.query.filter_by(lecture_no=lecture_no).filter(Assignment.assignment_no <= assignment_no).all()
    now_assignment = assignments[-1]
    res = []
    data = dict()
    if is_self:
        data["name"] = "자습"
    else:
        data["name"] = attendee.user.name
    data["data"] = []
    for index, assignment in enumerate(assignments, start=1):  # start=1로 설정하여 1부터 시작
            if is_self:
                if now_assignment.as_type != assignment.as_type:
                    continue
            tmp = dict()
            tmp["name"] = str(index) + "회차"
            tmp["data"] = []
            for i in ["translation_error", "omission", "expression", "intonation", "grammar_error", "others"]:
                query = Feedback2.query.filter_by(
                    lecture_no=lecture_no, 
                    assignment_no=assignment.assignment_no
                )
                if not is_self:
                    query = query.filter_by(attendee_no=attendee.attendee_no)
                value = query.with_entities(getattr(Feedback2, i)).scalar()
                value = 0.0 if value is None else float(value)
                tmp["data"].append(float(value))
            data["data"].append(tmp)
    data["data"] = data["data"][-3:]
    res.append(data)

    return res

def detail_accuracy(lecture_no:int, assignment_no:int):
    attendees = Attendee.query.filter_by(lecture_no=lecture_no).all()[1:]
    assignments = Assignment.query.filter_by(lecture_no=lecture_no).filter(Assignment.assignment_no <= assignment_no).all()

    res = []
    for attendee in attendees:
        data = dict()
        data["name"] = attendee.user.name
        data["data"] = []
        for index, assignment in enumerate(assignments, start=1):  # start=1로 설정하여 1부터 시작
            tmp = dict()
            tmp["name"] = str(index) + "회차"
            tmp["data"] = []
            for i in ["translation_error", "omission", "expression", "intonation", "grammar_error", "others"]:
                value = Feedback2.query.filter_by(
                    lecture_no=lecture_no, 
                    attendee_no=attendee.attendee_no,
                    assignment_no=assignment.assignment_no
                ).with_entities(getattr(Feedback2, i)).scalar()
                value = 0.0 if value is None else float(value)
                tmp["data"].append(float(value))
            data["data"].append(tmp)
        data["data"] = data["data"][-3:]
        res.append(data)

    return res

def get_zip_url(lecutre_no:int, user_no:int):
    lecutre = Lecture.query.filter_by(lecture_no=lecutre_no).first()
    attendee_no = Attendee.query.filter_by(lecture_no=lecutre_no, user_no=user_no).first().attendee_no
    user_name = User.query.filter_by(user_no=user_no).first().name
    assignments = Assignment.query.filter_by(lecture_no=lecutre_no).all()
    files = []
    for assignment in assignments:
        assignment_check = Assignment_check.query.filter_by(assignment_no=assignment.assignment_no, attendee_no=attendee_no).order_by(Assignment_check.check_no.desc()).first()
        if assignment_check is None:
            continue
        if assignment_check.ae_text != "" and assignment_check.ae_denotations != "" and assignment_check.ae_attributes != "":
            text_ae = make_json(assignment_check.ae_text, assignment_check.ae_denotations, assignment_check.ae_attributes)
            path = os.environ["UPLOAD_PATH"] + "/" + str(assignment.assignment_no) + "_" + assignment.as_name + "_" + str(user_name) + ".json"
            files.append(path)
            #json 파일 만들기
            with open(path, "w") as f:
                f.write(parse.unquote(text_ae))
        _,uuid=get_prob_wav_url(assignment.assignment_no,user_no,assignment.lecture_no)
        if uuid:
            text,denotations,attributes, index_len = "", [], [], 0
            Tid = 1
            for index,i in enumerate(uuid):
                stt_job_alias = aliased(SttJob)  # Aliasing for clarity if needed

                stt = (Stt.query
                    .join(stt_job_alias, stt_job_alias.stt_no == Stt.stt_no)  # Joining on stt_no
                    .filter(stt_job_alias.stt_no.isnot(None))  # Ensuring stt_job is not null
                    .filter(Stt.wav_file == i["uuid"], Stt.is_deleted == False)
                    .order_by(Stt.stt_no.desc())
                    .first())
                # stt=Stt.query.filter_by(wav_file=i["uuid"], is_deleted=False).order_by(Stt.stt_no.desc()).first()
                if stt is None:
                    print("stt is None")
                    continue
                stt_job=SttJob.query.filter_by(stt_no=stt.stt_no).first()
                if stt_job is None:
                    print("stt_job is None",stt.stt_no)
                    continue
                result=stt_job.stt_result
                path = os.environ["UPLOAD_PATH"] + "/" + str(assignment.assignment_no) + "_" + assignment.as_name+ "_" + str(user_name) + "_원본stt" + str(index) + ".json"
                files.append(path)
                #json 파일 만들기
                with open(path, "w") as f:
                    if result == None:
                        result = ""
                    f.write(result)
                # 합본 만들기 준비
                try:
                    stt_result=json.loads(stt_job.stt_result)
                except:
                    print(stt_job.stt_result)
                    continue
                text += stt_result["text"]
                for denotation in stt_result["denotations"]:
                    denotation["id"] = "T"+str(Tid)
                    Tid += 1
                    denotation["span"]["begin"] += index_len
                    denotation["span"]["end"] += index_len
                    denotations.append(denotation)
                # attributes += stt_result["attributes"]
                text += "---------------------------\n"
                index_len = len(text)
            # 합본 생성
            path = os.environ["UPLOAD_PATH"] + "/" + str(assignment.assignment_no) + "_" + assignment.as_name + "_" + str(user_name) + "_원본stt합본.json"
            with open(path, "w") as f:
                f.write(json.dumps({"text":text, "denotations":denotations, "attributes":attributes}, ensure_ascii=False))
            files.append(path)
            
                
        # file_count = len(Assignment_check_list.query.filter_by(check_no=assignment_check.check_no).all())
        # stts = Stt.query.filter_by(assignment_no=assignment.assignment_no, user_no=user_no).order_by(Stt.stt_no.desc()).all()[:file_count]
        # for index, stt in enumerate(stts[::-1]):
        #     stt_job = SttJob.query.filter_by(stt_no=stt.stt_no).first()
        #     if stt_job is None:
        #         continue
        #     result = stt_job.stt_result
        #     path = os.environ["UPLOAD_PATH"] + "/" + str(stt.stt_no) + "_" + str(user_name) + "_원본 stt" + str(index) + ".json"
        #     files.append(path)
        #     #json 파일 만들기
        #     with open(path, "w") as f:
        #         f.write(result)

    #zip 파일 만들기
    zip_path = os.environ["UPLOAD_PATH"] + "/" + str(lecutre_no) + "_" + lecutre.lecture_name  + "_" + str(user_name) + ".zip"
    with zipfile.ZipFile(zip_path, "w") as f:
        for file in files:
            f.write(file, os.path.basename(file))
    return zip_path