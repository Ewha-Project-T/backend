import json
from pickle import TRUE
from flask import jsonify,render_template, request, redirect, url_for,abort,make_response,flash,Flask
from flask_restful import reqparse, Resource
from worker import do_stt_work
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.assignment_service import assignment_cancel, assignment_chance, assignment_detail, assignment_detail_record, assignment_detail_translate, assignment_end_submission, assignment_record, assignment_self_detail, assignment_self_detail_record, assignment_self_record, assignment_translate, delete_self_assignment, edit_assignment, get_assignment, get_assignments_manage, get_calendar, get_date, get_self_assignment,mod_assignment_listing,check_assignment,make_as, create_assignment,prob_list_professor, prob_list_student, mod_as,delete_assignment,get_as_name,get_prob_wav_url,get_wav_url,get_stt_result,get_original_stt_result,get_as_info,get_feedback,make_json_url, prob_self_list,save_json_feedback,get_prob_submit_list,get_studentgraph,get_professorgraph
from ..services.lecture_service import lecture_access_check
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from os import environ as env
from datetime import datetime
import os
import uuid


host_url=env["HOST"]
perm_list={"학생":1,"조교":2,"교수":3}


#app = Flask(__name__)
#CORS(app)  # CORS 확장 추가

class React_Prob_student(Resource):
    @jwt_required()
    def get(self):#과제리스트
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        return jsonify(prob_list_student(lecture_no,user_info["user_no"]))
    
class React_Porb_professor(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']

        return jsonify(prob_list_professor(lecture_no,user_info["user_no"]))
    
class React_Prob_Self(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        return jsonify(prob_self_list(user_info["user_no"]))
    
class React_Prob_add(Resource):
    @jwt_required()
    def post(self):#과제만들기 #자습용과제 기능에따라 달라질수있으므로 보류
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('prob_timeEnd', type=str,  required=True, help="limit_time is required")
        parser.add_argument('prob_name', type=str, required=True, help="as_name is required")
        parser.add_argument('prob_type', type=str, required=True, help="as_type is required")
        parser.add_argument('prob_keyword', type=str)
        parser.add_argument('prob_translang_source',type=str)
        parser.add_argument('prob_translang_destination',type=str)
        parser.add_argument('prob_exp', type=str)
        parser.add_argument('prob_replay', type=str)
        parser.add_argument('prob_play_speed', type=str)
        parser.add_argument('prob_open', type=str)
        parser.add_argument('prob_region', type=str, action='append')
        parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        args=parser.parse_args()
        lecture_no = args['lecture_no']
        week = args['prob_week']
        limit_time = args['prob_timeEnd']
        as_name = args['prob_name']
        as_type = args['prob_type']
        keyword = args['prob_keyword']
        prob_translang_source=args['prob_translang_source']
        prob_translang_destination=args['prob_translang_destination']
        description = args['prob_exp']
        re_limit = args['prob_replay']
        speed = args['prob_play_speed']
        if(speed==""):
            speed=1
        disclosure = args['prob_open']
        upload_path= args['prob_sound_path']
        if(disclosure=="on"):
            disclosure=0
        else:
            disclosure=1
        prob_region=args['prob_region']
        user_info=get_jwt_identity()
        original_text = args['original_text']
        original_text=original_text.replace("<","&lt")
        original_text=original_text.replace(">","&gt")
        make_as(user_info["user_no"],lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text,upload_path,prob_region,user_info,prob_translang_source,prob_translang_destination)
        return{"msg" : "success","probcreateSuccess":1},200

class React_prob_handle(Resource):
    #TODO: 검증 추가 필요
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        assignment, prob_split_region = get_assignment(as_no)
        assignment = assignment.to_dict()
        assignment["prob_split_region"] = prob_split_region
        return jsonify({
            "assignment": assignment,
            "isSuccess": True,
        })
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        user_info=get_jwt_identity()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('limit_time', type=str,  required=True, help="limit_time is required")
        parser.add_argument('as_name', type=str, required=True, help="as_name is required")
        parser.add_argument('as_type', type=str, required=True, help="as_type is required")
        parser.add_argument('keyword', type=str)
        parser.add_argument('prob_translang_source',type=str)
        parser.add_argument('prob_translang_destination',type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('speed', type=float)
        parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        parser.add_argument('prob_split_region', type=str, action='append') # 음성파일 분할된 구간
        parser.add_argument('assign_count', type=int)
        parser.add_argument('keyword_open', type=int)
        parser.add_argument('open_time', type=str)
        parser.add_argument('file_name', type=str)
        parser.add_argument('file_path', type=str)
        args=parser.parse_args()
        lecture_no = args['lecture_no']
        limit_time = args['limit_time']
        as_name = args['as_name']
        as_type = args['as_type']
        keyword = args['keyword']
        prob_translang_source=args['prob_translang_source']
        prob_translang_destination=args['prob_translang_destination']
        description = args['description']
        speed = args['speed']
        original_text = args['original_text']
        prob_sound_path = args['prob_sound_path']
        prob_split_region=args['prob_split_region']
        assign_count=args['assign_count']
        keyword_open=args['keyword_open']
        open_time=args['open_time']
        file_name=args['file_name']
        file_path=args['file_path']
        new_assignmen_no = create_assignment(lecture_no,limit_time,as_name,as_type,keyword,prob_translang_source,prob_translang_destination,description,speed,original_text,prob_sound_path,prob_split_region,assign_count,open_time,file_name,file_path,user_info,keyword_open)
        if new_assignmen_no is None:
            return jsonify({
                "msg" : "파일이 존재하지 않습니다.",
                "isSuccess": False,
            }), 400
        return jsonify({
            "msg" : "success",
            "isSuccess": True,
            "new_assignmen_no": new_assignmen_no,
        })
    @jwt_required()
    def put(self):
        parser = reqparse.RequestParser()
        user_info=get_jwt_identity()
        
        parser.add_argument('as_no', type=int)
        parser.add_argument('limit_time', type=str,  required=True, help="limit_time is required")
        parser.add_argument('as_name', type=str, required=True, help="as_name is required")
        parser.add_argument('as_type', type=str, required=True, help="as_type is required")
        parser.add_argument('keyword', type=str)
        parser.add_argument('prob_translang_source',type=str)
        parser.add_argument('prob_translang_destination',type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('speed', type=float)
        parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        parser.add_argument('prob_split_region', type=str, action='append') # 음성파일 분할된 구간
        parser.add_argument('assign_count', type=int)
        parser.add_argument('keyword_open', type=int)
        parser.add_argument('open_time', type=str)
        parser.add_argument('file_name', type=str)
        parser.add_argument('file_path', type=str)
        args=parser.parse_args()
        as_no = args['as_no']
        limit_time = args['limit_time']
        as_name = args['as_name']
        as_type = args['as_type']
        keyword = args['keyword']
        prob_translang_source=args['prob_translang_source']
        prob_translang_destination=args['prob_translang_destination']
        description = args['description']
        speed = args['speed']
        original_text = args['original_text']
        prob_sound_path = args['prob_sound_path']
        prob_split_region=args['prob_split_region']
        assign_count=args['assign_count']
        keyword_open=args['keyword_open']
        open_time=args['open_time']
        file_name=args['file_name']
        file_path=args['file_path']
        edit_prob = edit_assignment(as_no,limit_time,as_name,as_type,keyword,prob_translang_source,prob_translang_destination,description,speed,original_text,prob_sound_path,prob_split_region,assign_count,open_time,file_name,file_path,user_info,keyword_open)
        if edit_prob is None:
            return jsonify({
                "msg" : "과제가 없거나, 파일이 존재하지 않습니다.",
                "isSuccess": False,
            }), 400
        return jsonify({
            "msg" : "success",
            "isSuccess": True,
            "edit_prob": edit_prob,
        })
    @jwt_required()
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        delete_assignment(as_no)
        return jsonify({
            "msg" : "success",
            "isSuccess": True,
        })
    
class React_self_prob_handle(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        user_info=get_jwt_identity()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        assignment, prob_split_region = get_self_assignment(as_no, user_info["user_no"])
        if assignment is None:
            return jsonify({
                "msg" : "과제에 접근할 수 없습니다.",
                "isSuccess": False,
            })
        assignment = assignment.to_dict()
        assignment["prob_split_region"] = prob_split_region
        return jsonify({
            "assignment": assignment,
            "isSuccess": True,
        })
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        user_info=get_jwt_identity()
        # parser.add_argument('limit_time', type=str,  required=True, help="limit_time is required")
        parser.add_argument('as_name', type=str, required=True, help="as_name is required")
        parser.add_argument('as_type', type=str, required=True, help="as_type is required")
        parser.add_argument('keyword', type=str)
        parser.add_argument('prob_translang_source',type=str)
        parser.add_argument('prob_translang_destination',type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('speed', type=float)
        parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        parser.add_argument('prob_split_region', type=str, action='append') # 음성파일 분할된 구간
        # parser.add_argument('assign_count', type=int)
        # parser.add_argument('keyword_open', type=int)
        # parser.add_argument('open_time', type=str)
        parser.add_argument('file_name', type=str)
        parser.add_argument('file_path', type=str)
        args=parser.parse_args()
        limit_time = None
        as_name = args['as_name']
        as_type = args['as_type']
        keyword = args['keyword']
        prob_translang_source=args['prob_translang_source']
        prob_translang_destination=args['prob_translang_destination']
        description = args['description']
        speed = args['speed']
        original_text = args['original_text']
        prob_sound_path = args['prob_sound_path']
        prob_split_region=args['prob_split_region']
        assign_count=2100000000
        keyword_open=1
        open_time=None
        file_name=args['file_name']
        file_path=args['file_path']
        new_assignmen_no = create_assignment(0,limit_time,as_name,as_type,keyword,prob_translang_source,prob_translang_destination,description,speed,original_text,prob_sound_path,prob_split_region,assign_count,open_time,file_name,file_path,user_info,keyword_open, True)
        if new_assignmen_no is None:
            return jsonify({
                "msg" : "파일이 존재하지 않습니다.",
                "isSuccess": False,
            }), 400
        return jsonify({
            "msg" : "success",
            "isSuccess": True,
            "new_assignmen_no": new_assignmen_no,
        })
    @jwt_required()
    def put(self):
        parser = reqparse.RequestParser()
        user_info=get_jwt_identity()
        
        parser.add_argument('as_no', type=int)
        # parser.add_argument('limit_time', type=str,  required=True, help="limit_time is required")
        parser.add_argument('as_name', type=str, required=True, help="as_name is required")
        parser.add_argument('as_type', type=str, required=True, help="as_type is required")
        parser.add_argument('keyword', type=str)
        parser.add_argument('prob_translang_source',type=str)
        parser.add_argument('prob_translang_destination',type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('speed', type=float)
        parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        parser.add_argument('prob_split_region', type=str, action='append') # 음성파일 분할된 구간
        # parser.add_argument('assign_count', type=int)
        # parser.add_argument('keyword_open', type=int)
        # parser.add_argument('open_time', type=str)
        parser.add_argument('file_name', type=str)
        parser.add_argument('file_path', type=str)
        args=parser.parse_args()
        as_no = args['as_no']
        limit_time = datetime.now()
        as_name = args['as_name']
        as_type = args['as_type']
        keyword = args['keyword']
        prob_translang_source=args['prob_translang_source']
        prob_translang_destination=args['prob_translang_destination']
        description = args['description']
        speed = args['speed']
        original_text = args['original_text']
        prob_sound_path = args['prob_sound_path']
        prob_split_region=args['prob_split_region']
        assign_count=2_100_000_000
        keyword_open=1
        open_time=datetime.now()
        file_name=args['file_name']
        file_path=args['file_path']
        edit_prob = edit_assignment(as_no,limit_time,as_name,as_type,keyword,prob_translang_source,prob_translang_destination,description,speed,original_text,prob_sound_path,prob_split_region,assign_count,open_time,file_name,file_path,user_info,keyword_open, True)
        if edit_prob is None:
            return jsonify({
                "msg" : "과제가 없거나, 파일이 존재하지 않습니다.",
                "isSuccess": False,
            }), 400
        return jsonify({
            "msg" : "success",
            "isSuccess": True,
            "edit_prob": edit_prob,
        })
    @jwt_required()
    def delete(self):
        parser = reqparse.RequestParser()
        user_info=get_jwt_identity()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        if delete_self_assignment(as_no, user_info["user_no"]) == None:
            return jsonify({
                "msg" : "과제에 접근할 수 없습니다.",
                "isSuccess": False,
            })
        
        return jsonify({
            "msg" : "success",
            "isSuccess": True,
        })
        
class React_Prob_detail(Resource):
        @jwt_required()
        def get(self):
            user_info=get_jwt_identity()
            parser = reqparse.RequestParser()
            parser.add_argument('as_no', type=int)
            args = parser.parse_args()
            as_no = args['as_no']
            res = assignment_detail(as_no, user_info["user_no"])
            if res is None:
                return jsonify({
                    "msg" : "수강하지 않은 학생입니다.",
                    "isSuccess": False,
                })
            return jsonify(res)
        
class React_Prob_self_detail(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        res = assignment_self_detail(as_no, user_info["user_no"])
        if res is None:
            return jsonify({
                "msg" : "본인 자습이 아닙니다.",
                "isSuccess": False,
            })
        return jsonify(res)
        
class React_Prob_record(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        res = assignment_detail_record(as_no, user_info["user_no"])
        if res.get("message") :
            print("error",res)
            return res
        return jsonify(res)
    @jwt_required()
    def post(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        parser.add_argument('prob_submit_list', type=str, action='append')
        args = parser.parse_args()
        as_no = args['as_no']
        prob_submit_list = args['prob_submit_list']
        res = assignment_record(as_no, user_info["user_no"], prob_submit_list)
        if not res.get("submission_count") :
            return jsonify(res), 401
        return jsonify(res)
    
class React_Prob_self_record(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        res = assignment_self_detail_record(as_no, user_info["user_no"])
        if res.get("message") :
            return res
        return jsonify(res)
    @jwt_required()
    def post(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        parser.add_argument('prob_submit_list', type=str, action='append')
        args = parser.parse_args()
        as_no = args['as_no']
        prob_submit_list = args['prob_submit_list']
        res = assignment_self_record(as_no, user_info["user_no"], prob_submit_list)
        if res.get("isSuccess") == False:
            return jsonify(res), 401
        return jsonify(res)
    
class React_Prob_end_submission(Resource):
    @jwt_required()
    def put(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        res = assignment_end_submission(as_no, user_info["user_no"])
        if not res.get("submission_count") :
            return res, 200
        return jsonify(res)
    
class React_Prob_self_end_submission(Resource):
    @jwt_required()
    def put(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        res = assignment_end_submission(as_no, user_info["user_no"], True)
        if not res.get("submission_count") :
            return res, 200
        return jsonify(res)

class React_Prob_submit_list(Resource):
        @jwt_required()
        def get(self):
            parser = reqparse.RequestParser()
            parser.add_argument('lecture_no', type=int)
            parser.add_argument('as_no', type=int)
            args = parser.parse_args()
            as_no=args['as_no']
            lecture_no = args['lecture_no']
            user_info=get_jwt_identity()
            user_list=get_prob_submit_list(as_no,lecture_no)
            return jsonify({   "userInfo":user_info,
                    "userList": user_list,
                    "as_no" : as_no,
                    "lecture_no" : lecture_no,
                })

class React_Prob_submit_list2(Resource):
        @jwt_required()
        def get(self):
            parser = reqparse.RequestParser()
            parser.add_argument('as_no', type=int)
            args = parser.parse_args()
            as_no=args['as_no']
            user_info=get_jwt_identity()
            user_list=get_assignments_manage(user_info, as_no)
            return jsonify({   "userInfo":user_info,
                })

class React_Prob_submit(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        as_info=get_as_info(lecture_no,as_no)
        user_info=get_jwt_identity()
        if(as_info['as_type']=="번역"):
            return jsonify({   
                    "userlist":user_info,
                    "lectureNo": lecture_no,
                    "as_no" : as_no,
                    "as_info" : as_info,
                })
        wav_url=get_wav_url(as_no)
        return jsonify({   
                    "userlist":user_info,
                    "lectureNo": lecture_no,
                    "as_no" : as_no,
                    "as_info" : as_info,
                    "wav_url" : wav_url
                })
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('submitUUID',type=str,action='append')
        parser.add_argument('text',type=str)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        uuid=args['submitUUID']
        user_info=get_jwt_identity()
        if(uuid[0]=="0"):
            text=args['text']
            res = check_assignment(as_no,lecture_no,uuid,user_info,text)
            return jsonify(res)
        else:
            res = check_assignment(as_no,lecture_no,uuid,user_info)
            return jsonify(res)

class React_Prob_self_submit(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('submitUUID',type=str,action='append')
        parser.add_argument('text',type=str)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        uuid=args['submitUUID']
        user_info=get_jwt_identity()
        if(uuid[0]=="0"):
            text=args['text']
            res = check_assignment(as_no,lecture_no,uuid,user_info, text, True)
            return jsonify(res)
        else:
            res = check_assignment(as_no,lecture_no,uuid,user_info, "", True)
            return jsonify(res)

class Studentgraphlist(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        user_no = args['user_no']
        res=get_studentgraph(lecture_no,as_no,user_no)
        if(res==-1):
            return jsonify({"msg":"none feedback", "feedbackReadSuccess" : 0})
        return jsonify(res)
        
class Professorgraphlist(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        user_no = args['user_no']
        res=get_professorgraph(lecture_no,as_no,user_no)
        return jsonify(res)

class TranslateAssignment(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        res = assignment_detail_translate(as_no, user_info["user_no"])
        if res.get("message") :
            print("error",res)
            return res
        return jsonify(res)
    @jwt_required()
    def post(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        parser.add_argument('translate_text', type=str)
        args = parser.parse_args()
        as_no = args['as_no']
        translate_text = args['translate_text']
        res = assignment_translate(as_no, user_info["user_no"], translate_text)
        if res.get("isSuccess") == False:
            return jsonify(res)
        return jsonify(res)

class TranslateSelfAssignment(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        res = assignment_detail_translate(as_no, user_info["user_no"], True)
        if res.get("message") :
            print("error",res)
            return res
        return jsonify(res)
    @jwt_required()
    def post(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        parser.add_argument('translate_text', type=str)
        args = parser.parse_args()
        as_no = args['as_no']
        translate_text = args['translate_text']
        res = assignment_translate(as_no, user_info["user_no"], translate_text, True)
        if res.get("isSuccess") == False:
            return jsonify(res)
        return jsonify(res)    

class React_Cancel_prob(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        student_no = args['user_no']
        user_info=get_jwt_identity()
        res = assignment_cancel(as_no, user_info["user_no"], student_no)
        return jsonify(res)
    
class React_Cancel_self_prob(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        user_info=get_jwt_identity()
        res = assignment_cancel(as_no, user_info["user_no"])
        return jsonify(res)

class React_Chance_prob(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        args = parser.parse_args()
        as_no = args['as_no']
        student_no = args['user_no']
        user_info=get_jwt_identity()
        res = assignment_chance(as_no, user_info["user_no"], student_no)
        return jsonify(res)

class React_Prob_calendar(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('date', type=str)
        args = parser.parse_args()
        date = args['date']
        res = get_calendar(user_info, date)

        return jsonify(res)

class React_Prob_date(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('date', type=str)
        args = parser.parse_args()
        date = args['date']
        res = get_date(user_info, date)

        return jsonify(res)

###사용중이라고 주석남기셔서 옮겨둡니다.
ALLOWED_SOUND_EXTENSIONS = {'mp3'}
def allowed_sound_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_SOUND_EXTENSIONS



class prob_upload(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('prob_sound', type=FileStorage, location='files')

    @jwt_required()
    def post(self):
        args = self.parser.parse_args()        
        file = args['prob_sound']

        if not file or not allowed_sound_file(file.filename) or not self.is_mp3(file):
            return {"msg": "mp3 file upload fail"}, 400

        filename = str(uuid.uuid4())
        path = f'{os.environ["UPLOAD_PATH"]}/{filename}.mp3'
        file.save(path)
        return jsonify({
            "file_path": path  # 추후 파일명에 대한 해쉬처리 필요
        })

    @staticmethod
    def is_mp3(f):
        """Check if the file has an MP3 signature."""
        f.seek(0)  # Ensure we're reading from the beginning
        header = f.read(3)
        return header == b'ID3' or header[:2] == b'\xff\xfb' or header[:2]==b'\xff\xf2' or header[:2]==b'\xff\xf3'

ALLOWED_EXTENSIONS = {'hwp','pdf','docx','doc','ppt','pptx','xls','xlsx','txt'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#pdf, docx upload
class prob_upload_file(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()      
        parser.add_argument('prob_file', type=FileStorage, location='files')        
        args = parser.parse_args()        
        file= args['prob_file']

        uuid_str=str(uuid.uuid4())
        filename = uuid_str
        file_extention = os.path.splitext(file.filename)[1].lower()
        path = f'{os.environ["UPLOAD_PATH"]}/{filename}{file_extention}'
        if file and allowed_file(file.filename):
            file.save(path)
        else:
            return {"msg":"file upload fail"},400
        res = {
            "file_path": path, #추후 파일명에대한 해쉬처리 필요
            "file_name": file.filename
        }
        return jsonify(res)