import ast
import json
from server import db
from .assignment_service import get_prob_wav_url, get_stt_result, make_json, make_json_url, parse_data
from ..model import Assignment_check, Assignment_check_list, Attendee, Assignment, Assignment_management, Feedback2, Lecture, Prob_region, Stt, SttJob, User
from sqlalchemy import func

def get_json_textae(as_no,user_no):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return "과제가 존재하지 않습니다.", False
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=assignment.lecture_no).first()
    if not attend:
        return "수강생이 아닙니다.", False
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    if not check:
        return "과제를 제출하지 않았습니다.", False
    assignment_management = Assignment_management.query.filter_by(assignment_no = as_no, attendee_no = attend.attendee_no).first()
    if(assignment_management==None):
        return "학생 정보가 존재하지 않습니다.", False
    if assignment_management.end_submission is False:
        return "학생이 최종 제출하지 않았습니다.", False
    if(check.ae_text == "" and check.ae_denotations == "" and check.ae_attributes == ""):
        _,uuid=get_prob_wav_url(as_no,user_no,assignment.lecture_no)
        # stt_result,stt_feedback=get_stt_result(uuid)
        text,denotations,attributes = get_stt_result(uuid)
        if(text==None):
            return "STT 작업중 입니다.", False
        if(text==-1):
            return "STT 오류!!", False
        check.ae_text,check.ae_denotations,check.ae_attributes=text,denotations,attributes
        db.session.commit()
        # text,denotations,attributes=parse_data(stt_result,stt_feedback)
        # url=make_json_url(text,denotations_json,attributes_json,check,1)
        # textae = make_json(text,denotations_json,attributes_json)
    else:
        text,denotations,attributes = check.ae_text,check.ae_denotations,check.ae_attributes
        # url=make_json_url(check.ae_text,check.ae_denotations, check.ae_attributes, check,0)
    textae = make_json(text,denotations, attributes)
    new_attribute = "A"+ str(find_max_attribute_number(ast.literal_eval(attributes))+1)

    return textae, new_attribute,assignment_management.review#json, 교수평가
# attribute = [{'id': 'A1', 'subj': 'T1', 'pred': 'Unsure', 'obj': True}, {'id': 'A10', 'subj': 'T10', 'pred': 'Unsure', 'obj': True}, {'id': 'A11', 'subj': 'T11', 'pred': 'Unsure', 'obj': True}, {'id': 'A12', 'subj': 'T12', 'pred': 'Unsure', 'obj': True}, {'id': 'A13', 'subj': 'T13', 'pred': 'Unsure', 'obj': True}, {'id': 'A16', 'subj': 'T43', 'pred': 'Note', 'obj': 'asdfasdfasdfasdf'}, {'id': 'A2', 'subj': 'T2', 'pred': 'Unsure', 'obj': True}, {'id': 'A3', 'subj': 'T3', 'pred': 'Unsure', 'obj': True}, {'id': 'A4', 'subj': 'T4', 'pred': 'Unsure', 'obj': True}, {'id': 'A5', 'subj': 'T5', 'pred': 'Unsure', 'obj': True}, {'id': 'A6', 'subj': 'T6', 'pred': 'Unsure', 'obj': True}, {'id': 'A7', 'subj': 'T7', 'pred': 'Unsure', 'obj': True}, {'id': 'A8', 'subj': 'T8', 'pred': 'Unsure', 'obj': True}, {'id': 'A9', 'subj': 'T9', 'pred': 'Unsure', 'obj': True}]
def find_max_attribute_number(attributes):
    max_attribute = 0
    for attribute in attributes:
        if int(attribute['id'][1:]) > max_attribute:
            max_attribute = int(attribute['id'][1:])
    return max_attribute

def put_json_textae(as_no,user_no,ae_denotations,ae_attributes):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return "과제가 존재하지 않습니다.", False
    attend=Attendee.query.filter_by(user_no=user_no,lecture_no=assignment.lecture_no).first()
    if not attend:
        return "수강생이 아닙니다.", False
    check=Assignment_check.query.filter_by(assignment_no=as_no,attendee_no=attend.attendee_no,assignment_check=1).order_by(Assignment_check.check_no.desc()).first()
    if not check:
        return "과제를 제출하지 않았습니다.", False
    assignment_management = Assignment_management.query.filter_by(assignment_no = as_no, attendee_no = attend.attendee_no).first()
    if(assignment_management==None):
        return "학생 정보가 존재하지 않습니다.", False
    if assignment_management.end_submission is False:
        return "학생이 최종 제출하지 않았습니다.", False

    if ae_denotations != "None":
        ae_denotations = str(sorted(ast.literal_eval(ae_denotations), key=donotations_sort_key)) # sort by begin, end
        check.ae_denotations = ae_denotations
    if ae_attributes != "None":
        check.ae_attributes = ae_attributes
    db.session.commit()
    return "success", True

def donotations_sort_key(item):
    return (item['span']['begin'], item['span']['end'])

def get_feedback_info(as_no: int, student_no: int, user_no: int):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if assignment.user_no != user_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    
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
    assignment_audio = Prob_region.query.filter_by(assignment_no=as_no).all()
    if not assignment_audio:
        return {"message": "해당 과제의 오디오 파일이 존재하지 않습니다.", "isSuccess": False}
    assignment_check_list = Assignment_check_list.query.filter_by(check_no=assignment_check.check_no).all()
    if not assignment_check_list:
        return {"message": "해당 학생의 오디오 파일이 존재하지 않습니다.", "isSuccess": False}
    stt = Stt.query.filter_by(assignment_no=as_no, user_no = user_no).all()
    text,denotations_json,attributes_json ="",[],[]
    for st in stt:
        stt_job = SttJob.query.filter_by(stt_no=st.stt_no).first()
        if stt_job is None:
            return {"message": "교수님의 음원 STT 작업 진행중입니다.", "isSuccess": False}
        result = json.loads(stt_job.stt_result)
        text += result["text"]
        # denotations_json += result["denotations"]
        # attributes_json += result["attributes"]

    res = dict()
    # res["original_ae"] = json.loads(make_json(text, denotations_json, attributes_json))
    res["original_tts"] = text
    res["original_text"] = assignment.original_text
    res["student_name"] = user.name
    res["submit_time"] = assignment_manage.end_submission_time
    res["limit_time"] = assignment.limit_time

    res["assignment_audio"] = [make_audio_format(assignment_audio) for assignment_audio in assignment_audio]
    res["student_audio"] = [make_audio_format(assignment_check_list, index) for index, assignment_check_list in enumerate(assignment_check_list)]
    res["isSuccess"] = True
    
    return res

def make_audio_format(prob_region, id=0):
    url = prob_region.upload_url if hasattr(prob_region, "upload_url") else prob_region.acl_uuid
    return {
            "label": "원문 구간 " + str(prob_region.region_index)  if hasattr(prob_region, "region_index") else "학생 구간" + str(id),
            # "label": int(prob_region.region_index) if hasattr(prob_region, "region_index") else id,
            "value": "./upload/" + url + ".mp3",
    }

def get_feedback_review(as_no:int, student_no:int,user_no:int):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, user_no=student_no).first()
    if not attendee:
        return {"message": "해당 강의를 수강한 학생이 아닙니다.", "isSuccess": False}
    assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no, attendee_no = attendee.attendee_no).first()
    if assignment.user_no != user_no or assignment_manage.attendee_no != attendee.attendee_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    if assignment_manage.end_submission is False:
        return {"message": "아직 과제가 제출되지 않았습니다.", "isSuccess": False}
    if assignment_manage.review is False and assignment_manage.attendee_no == attendee.attendee_no:
        return {"message": "교수의 피드백이 아직 제출되지 않았습니다.", "isSuccess": False}
    res = dict()
    res["review"] = assignment_manage.review
    return res

def save_feedback_review(as_no:int, student_no:int, user_no:int,review:str):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if not assignment.user_no == user_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, user_no=student_no).first()
    if not attendee:
        return {"message": "해당 강의를 수강한 학생이 아닙니다.", "isSuccess": False}
    assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no, attendee_no = attendee.attendee_no).first()
    assignment_manage.review = review
    db.session.commit()
    return {"message": "피드백이 저장되었습니다.", "isSuccess": True}

def get_all_graphs(as_no:int, user_no:int):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    # if not assignment.user_no == user_no:
    #     return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    lecture = Lecture.query.filter_by(lecture_no=assignment.lecture_no).first()
    if not lecture:
        return {"message": "해당 강의가 존재하지 않습니다.", "isSuccess": False}
    res = {
        "Delivery" : avg_delivery(lecture.lecture_no, assignment.assignment_no),
        "Accuracy" : avg_accuracy(lecture.lecture_no, assignment.assignment_no),
        "isSuccess": True,
    }
    return res

def avg_delivery(lecture_no:int, assingment_no:int):
    attendees = Attendee.query.filter_by(lecture_no=lecture_no).all()[1:]
    res = []
    for attendee in attendees:
        data = dict()
        data["name"] = attendee.user.name
        data["data"] = []
        print(attendee.user.name)
        for i in ["silence", "filler", "backtracking", "others"]:
            value = Feedback2.query.filter_by(
                lecture_no=lecture_no, 
                attendee_no=attendee.attendee_no
            ).filter(Feedback2.assignment_no <= assingment_no
                     ).with_entities(func.avg(getattr(Feedback2, i))).scalar()
            
            # value가 None인지 확인하고, None인 경우 0.0으로 설정
            value = 0.0 if value is None else float(value)
            data["data"].append(float(value))
        res.append(data)
    return res

def avg_accuracy(lecture_no:int, assingment_no:int):
    attendees = Attendee.query.filter_by(lecture_no=lecture_no).all()[1:]
    res = []
    for attendee in attendees:
        data = dict()
        data["name"] = attendee.user.name
        data["data"] = []
        for i in ["translation_error", "omission", "expression", "intonation", "grammar_error", "others"]:
            value = Feedback2.query.filter_by(
                lecture_no=lecture_no, 
                attendee_no=attendee.attendee_no
            ).filter(Feedback2.assignment_no <= assingment_no
                     ).with_entities(func.avg(getattr(Feedback2, i))).scalar()
            value = 0.0 if value is None else float(value)
            data["data"].append(float(value))
        res.append(data)
    return res