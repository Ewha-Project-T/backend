import json
from pickle import TRUE
from flask import jsonify,render_template, request, redirect, url_for,abort,make_response,flash,Flask
from flask_restful import reqparse, Resource
from worker import do_stt_work
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.assignment_service import assignment_detail,mod_assignment_listing,check_assignment,make_as,prob_listing, mod_as,delete_assignment,get_as_name,get_prob_wav_url,get_wav_url,get_stt_result,get_original_stt_result,get_as_info,get_feedback,make_json_url,get_json_feedback,save_json_feedback,get_prob_submit_list,get_studentgraph,get_professorgraph
from ..services.lecture_service import lecture_access_check
from ..services.login_service import admin_required, professor_required, assistant_required
from werkzeug.utils import secure_filename
from os import environ as env
import os
import uuid


host_url=env["HOST"]
perm_list={"학생":1,"조교":2,"교수":3}


#app = Flask(__name__)
#CORS(app)  # CORS 확장 추가

class React_Prob(Resource):
    @jwt_required()
    def get(self):#과제리스트
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        prob_list=prob_listing(lecture_no,user_info["user_no"])
        return jsonify( 
            {
            "number" : 1,
            "list":prob_list["1"],
            },
            {
            "number" : 2,
            "list":prob_list["2"],
            },
            {
            "number" : 3,
            "list":prob_list["3"],
            },
            {
            "number" : 4,
            "list":prob_list["4"],
            },
            {
            "number" : 5,
            "list":prob_list["5"],
            },
            {
            "number" : 6,
            "list":prob_list["6"],
            },
            {
            "number" : 7,
            "list":prob_list["7"],
            },
            {
            "number" : 8,
            "list":prob_list["8"],
            },
            {
            "number" : 9,
            "list":prob_list["9"],
            },
            {
            "number" : 10,
            "list":prob_list["10"],
            },
            {
            "number" : 11,
            "list":prob_list["11"],
            },
            {
            "number" : 12,
            "list":prob_list["12"],
            },
            {
            "number" : 13,
            "list":prob_list["13"],
            },
            {
            "number" : 14,
            "list":prob_list["14"],
            },
            {
            "number" : 15,
            "list":prob_list["15"],
            },
            {
            "number" : 16,
            "list":prob_list["16"],
            }, 
            {
            "user_no": user_info["user_no"]  # user_no 값을 추가
            })
    
class React_Prob_add(Resource):
    @jwt_required()#자습용과제 기능에따라 달라질수있으므로 보류
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        user_info=get_jwt_identity()
        return make_response(render_template("prob_add.html",lecture_no=lecture_no,user_info=user_info))
    @jwt_required()
    def post(self):#과제만들기 #자습용과제 기능에따라 달라질수있으므로 보류
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('prob_week', type=str, required=True, help="week is required")
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

class React_Prob_del(Resource):
    @jwt_required()
    def get(self):#과제 삭제
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        as_no = args['as_no']
        user_info=get_jwt_identity()
        if(lecture_access_check(user_info["user_no"],lecture_no) or user_info["user_perm"]==0):
            delete_assignment(as_no)
            return{"msg" : "assignment delete success","probdeleteSuccess":1},200
        else:
            return{"msg": "access denied"}
        
class React_Prob_mod(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        as_no = args['as_no']
        as_list,audio_list=mod_assignment_listing(lecture_no,as_no)
        user_info=get_jwt_identity()
        return jsonify({   "userlist":user_info,
                    "lectureNo": lecture_no,
                    "as_no" : as_no,
                    "as_list" : as_list,
                    "audio_list": audio_list,
                })
    @jwt_required()
    def post(self):#강의수정권한관리 만든사람, 관리자
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('prob_week', type=str)
        parser.add_argument('prob_timeEnd', type=str)
        parser.add_argument('prob_name', type=str)
        parser.add_argument('prob_type', type=str)
        parser.add_argument('prob_keyword', type=str)
        parser.add_argument('prob_translang_source',type=str)
        parser.add_argument('prob_translang_destination',type=str)
        parser.add_argument('prob_exp', type=str)
        parser.add_argument('prob_replay', type=str)
        parser.add_argument('prob_play_speed')
        parser.add_argument('prob_open', type=str)
        parser.add_argument('prob_region', type=str, action='append')
        parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        args=parser.parse_args()
        lecture_no = args['lecture_no']
        as_no= args['as_no']
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
        disclosure = args['prob_open']
        upload_path= args['prob_sound_path']
        if(disclosure=="on"):
            disclosure=0
        else:
            disclosure=1
        prob_region=args['prob_region']
        original_text = args['original_text']
        original_text=original_text.replace("<","&lt")
        original_text=original_text.replace(">","&gt")
        user_info=get_jwt_identity()
        if(lecture_access_check(user_info["user_no"],lecture_no) or user_info["user_perm"]==0):
            mod_as(lecture_no,as_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text,upload_path,prob_region,user_info,prob_translang_source,prob_translang_destination)
            return{"msg" : "assignment modify success","assignmentmodifySuccess" : 1},200
        else:
            return{"msg": "access denied"}
        
class React_Prob_detail(Resource):
        @jwt_required()
        def get(self):
            user_info=get_jwt_identity()
            parser = reqparse.RequestParser()
            parser.add_argument('as_no', type=int)
            args = parser.parse_args()
            as_no = args['as_no']
            res = assignment_detail(as_no, user_info["user_no"])
            return jsonify({   
                    "keyword" : res["keyword"],
                    "detail" : res["detail"],
                    "limit_time" : res["limit_time"],
                    "assign_count" : res["assign_count"],
                    "my_count" : res["my_count"],
                    "feedback" : res["feedback"],
                    "end_submission": res["end_submission"],
                    "open_time" : res["open_time"]
                })

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
            check_assignment(as_no,lecture_no,uuid,user_info,text)
            return jsonify({"SubmitSuccess" : 1})
        else:
            check_assignment(as_no,lecture_no,uuid,user_info)
            return jsonify({"SubmitSuccess" : 1})

# class Feedback(Resource):
#     @jwt_required()
#     def get(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('lecture_no', type=int)
#         parser.add_argument('as_no', type=int)
#         parser.add_argument('user_no', type=int)
#         args = parser.parse_args()
#         as_no=args['as_no']
#         lecture_no = args['lecture_no']
#         user_no = args['user_no']
#         url,review=get_json_feedback(as_no,lecture_no,user_no)
#         if(url=="error:stt"):
#             return jsonify({"FeedbackStatus":3})
#         if(url=="error:nocheck"):
#             return jsonify({"FeedbackStatus":2})
#         return jsonify({"url":url,"message":review,"FeedbackStatus":1})

#     @jwt_required()
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('lecture_no', type=int)
#         parser.add_argument('as_no', type=int)
#         parser.add_argument('user_no', type=int)
#         parser.add_argument('textAE', type=str)
#         parser.add_argument('result', type=str) # 총평
#         parser.add_argument('DeliverIndividualList', type=int, action='append')
#         parser.add_argument('ContentIndividualList', type=int, action='append')
#         args = parser.parse_args()
#         as_no=args['as_no']
#         lecture_no = args['lecture_no']
#         user_no = args['user_no']
#         text=args['textAE']
#         result=args['result']
#         dlist=args['DeliverIndividualList']
#         clist=args['ContentIndividualList']
#         save_json_feedback(as_no,lecture_no,user_no,text,result,dlist,clist)
#         return jsonify({"savesuccess" : 1})

class Feedback2(Resource):
    #TODO: api테스트 완료 후 jwt 적용
    # @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        user_no = args['user_no']
        url,review=get_json_feedback(as_no,lecture_no,user_no)
        if(url=="error:stt"):
            return jsonify({"FeedbackStatus":3})
        if(url=="error:nocheck"):
            return jsonify({"FeedbackStatus":2})
        return jsonify({"url":url,"review":review,"isSuccess":True})
    #TODO: api테스트 완료 후 jwt 적용
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        parser.add_argument('ae_denotations', type=str,action='append')
        parser.add_argument('ae_attributes', type=str, action='append')
        parser.add_argument('result', type=str) # 총평
        parser.add_argument('DeliverIndividualList', type=int, action='append')
        parser.add_argument('ContentIndividualList', type=int, action='append')
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        user_no = args['user_no']
        ae_denotations = str(args['ae_denotations']).replace('"',"")
        ae_attributes = str(args['ae_attributes']).replace('"',"")
        result=args['result']
        dlist=args['DeliverIndividualList']
        clist=args['ContentIndividualList']
        save_json_feedback(as_no,lecture_no,user_no,ae_attributes,ae_denotations,result,dlist,clist)
        return jsonify({"isSuccess":True})

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