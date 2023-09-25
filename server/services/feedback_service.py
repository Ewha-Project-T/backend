from ..model import Assignment_check, Assignment_check_list, Attendee, Assignment, Assignment_management, Prob_region, User

def get_feedback_info(as_no: int, student_no: int, user_no: int):
    assignment = Assignment.query.filter_by(assignment_no=as_no).first()
    if not assignment:
        return {"message": "과제가 존재하지 않습니다.", "isSuccess": False}
    if assignment.user_no != user_no:
        return {"message": "과제를 열람할 권한이 없습니다.", "isSuccess": False}
    attendee = Attendee.query.filter_by(lecture_no=assignment.lecture_no, attendee_no=student_no).first()
    if not attendee:
        return {"message": "해당 과제를 수강한 학생이 아닙니다.", "isSuccess": False}
    user = User.query.filter_by(user_no=attendee.user_no).first()
    assignment_manage = Assignment_management.query.filter_by(assignment_no=as_no, attendee_no = student_no).first()
    if assignment_manage.end_submission is False:
        return {"message": "아직 과제가 제출되지 않았습니다.", "isSuccess": False}
    assignment_check = Assignment_check.query.filter_by(assignment_no=as_no, attendee_no = student_no).order_by(Assignment_check.check_no.desc()).first()
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
            "id": int(prob_region.region_index) if hasattr(prob_region, "region_index") else id,
            "upload_url": "./upload/" + url,
    }