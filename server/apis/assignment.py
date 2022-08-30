from ast import keyword
import json
from pickle import TRUE
from flask import jsonify,render_template, request, redirect, url_for,abort,make_response
from flask_restful import reqparse, Resource
from worker import do_stt_work
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.assignment_service import prob_listing,make_as,mod_as,get_wav_url,delete_assignment,check_assignment,get_as_name,get_prob_wav_url,get_stt_result
from ..services.lecture_service import lecture_access_check
from werkzeug.utils import secure_filename
from os import environ as env
from werkzeug.datastructures import FileStorage
import os
import uuid

host_url=env["HOST"]
perm_list={"학생":1,"조교":2,"교수":3}

class Prob(Resource):
    @jwt_required()
    def get(self):#과제리스트
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        prob_list=prob_listing(lecture_no)
        return make_response(render_template("prob_list.html",prob_list=prob_list,lecture_no=lecture_no,user_perm=user_info["user_perm"]))

class Prob_add(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        return make_response(render_template("prob_add.html",lecture_no=lecture_no))
    @jwt_required()
    def post(self):#과제만들기
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('prob_week', type=str, required=True, help="week is required")
        parser.add_argument('prob_timeEnd', type=str,  required=True, help="limit_time is required")
        parser.add_argument('prob_name', type=str, required=True, help="as_name is required")
        parser.add_argument('prob_type', type=str, required=True, help="as_type is required")
        parser.add_argument('prob_keyword', type=str)
        parser.add_argument('prob_exp', type=str)
        parser.add_argument('prob_replay', type=str, required=True, help="re_limit is required")
        parser.add_argument('prob_play_speed', type=str, required=True, help="speed is required")
        parser.add_argument('prob_open', type=str)
        parser.add_argument('prob_region', type=str, action='append', required=True)
        #parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        args=parser.parse_args()
        lecture_no = args['lecture_no']
        week = args['prob_week']
        limit_time = args['prob_timeEnd']
        as_name = args['prob_name']
        as_type = args['prob_type']
        keyword = args['prob_keyword']
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
        user_info=get_jwt_identity()
        #original_text = args['original_text']
        make_as(lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,"",upload_path,prob_region,user_info)#original_text,upload_url
        return{"msg" : "success"},200

class Prob_mod(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        as_no = args['as_no']
        return make_response(render_template("prob_mod.html",lecture_no=lecture_no,as_no=as_no))
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
        parser.add_argument('prob_exp', type=str)
        parser.add_argument('prob_replay', type=str)
        parser.add_argument('prob_play_speed')
        parser.add_argument('prob_open', type=str)
        parser.add_argument('prob_region', type=str, action='append')
        #parser.add_argument('original_text', type=str)
        parser.add_argument('prob_sound_path', type=str)
        args=parser.parse_args()
        lecture_no = args['lecture_no']
        as_no= args['as_no']
        week = args['prob_week']
        limit_time = args['prob_timeEnd']
        as_name = args['prob_name']
        as_type = args['prob_type']
        keyword = args['prob_keyword']
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
        #original_text = args['original_text']
        user_info=get_jwt_identity()
        if(lecture_access_check(user_info["user_no"],lecture_no) or user_info["user_perm"]==0):
            mod_as(lecture_no,as_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,"",upload_path,prob_region,user_info)#original_text,upload_url
            return{"msg" : "assignment delete success"},200
        else:
            return{"msg": "access denied"}

class Prob_submit(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        wav_url=get_wav_url(as_no)
        return make_response(render_template("prob_submit.html",wav_url=wav_url,as_no=as_no,lecture_no=lecture_no))
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('submitUUID',type=str,action='append')
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        uuid=args['submitUUID']
        user_info=get_jwt_identity()
        check_assignment(as_no,lecture_no,uuid,user_info)
class Prob_del(Resource):
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
            return{"msg" : "assignment delete success"},200
        else:
            return{"msg": "access denied"}

class Prob_feedback(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        user_info=get_jwt_identity()
        as_name=get_as_name(as_no)
        wav_url,uuid=get_prob_wav_url(as_no,user_info,lecture_no)
        wav_url_example=get_wav_url(as_no)
        stt_result=get_stt_result(uuid)
        return make_response(render_template("prob_feedback.html",user_info=user_info,as_name=as_name,wav_url=wav_url,wav_url_example=wav_url_example,stt_result=stt_result))

ALLOWED_EXTENSIONS = {'wav','mp4'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class prob_upload(Resource):
    def post(self):
        parser = reqparse.RequestParser()      
        parser.add_argument('prob_sound', type=FileStorage, location='files')        
        args = parser.parse_args()        
        file= args['prob_sound']

        uuid_str=str(uuid.uuid4())
        filename = uuid_str
        path = f'{os.environ["UPLOAD_PATH"]}/{filename}.wav'
        if file and allowed_file(file.filename):
            #filename = secure_filename(file.filename)
            # file.save('./static/audio/{0}'.format(filename))
            file.save(path)
        
        # task = do_stt_work.delay(filename)
        res = {
            "file_path": path, #추후 파일명에대한 해쉬처리 필요
            # "job": task.id
        }
        return jsonify(res)

