import json
from server import db
from .assignment_service import get_prob_wav_url, get_stt_result, make_json_url, parse_data
from ..model import Assignment_check, Assignment_check_list, Attendee, Assignment, Assignment_management, Prob_region, User

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
        wav_url,uuid=get_prob_wav_url(as_no,user_no,assignment.lecture_no)
        stt_result,stt_feedback=get_stt_result(uuid)
        if(stt_result==None):
            return "error:stt", False
        text,denotations,attributes=parse_data(stt_result,stt_feedback)
        denotations_json = json.loads(denotations)
        attributes_json = json.loads(attributes)
        url=make_json_url(text,denotations_json,attributes_json,check,1)
    else:
        # utr=make_json(check.ae_text, check.ae_denotations, check.ae_attributes)
        url=make_json_url(check.ae_text,check.ae_denotations, check.ae_attributes, check,0)
    return url, assignment_management.review#json, 교수평가

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
    if ae_denotations:
        check.ae_denotations = ae_denotations
    if ae_attributes:
        check.ae_attributes = ae_attributes
    db.session.commit()
    return "success", True

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
    
    res = dict()
    res["original_text"] = assignment.original_text
    res["student_name"] = user.name
    res["submit_time"] = assignment_manage.end_submission_time
    res["limit_time"] = assignment.limit_time

    res["assignment_audio"] = [make_audio_format(assignment_audio) for assignment_audio in assignment_audio]
    res["student_audio"] = [make_audio_format(assignment_check_list, index) for index, assignment_check_list in enumerate(assignment_check_list)]

    
    return res

def make_audio_format(prob_region, id=0):
    url = prob_region.upload_url if hasattr(prob_region, "upload_url") else prob_region.acl_uuid + ".mp3"
    return {
            "name": "원문 구간 " + prob_region.region_index  if hasattr(prob_region, "region_index") else "학생 구간" + id,
            "label": int(prob_region.region_index) if hasattr(prob_region, "region_index") else id,
            "value": "./upload/" + url,
    }
