from ast import keyword
import json
from pickle import TRUE
from flask import jsonify,render_template, request, redirect, url_for,abort,make_response,flash
from flask_restful import reqparse, Resource
from worker import do_stt_work
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.assignment_service import prob_listing,make_as,mod_as,get_wav_url,delete_assignment,check_assignment,get_as_name,get_prob_wav_url,get_stt_result,get_original_stt_result,mod_assignment_listing,get_as_info,set_feedback,get_feedback,get_prob_submit_list
from ..services.lecture_service import lecture_access_check
from ..services.login_service import admin_required, professor_required, assistant_required
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
        prob_list=prob_listing(lecture_no,user_info["user_no"])
        return make_response(render_template("prob_list.html",prob_list1=prob_list["1"],prob_list2=prob_list["2"],prob_list3=prob_list["3"],prob_list4=prob_list["4"],prob_list5=prob_list["5"],prob_list6=prob_list["6"],prob_list7=prob_list["7"],prob_list8=prob_list["8"],prob_list9=prob_list["9"],prob_list10=prob_list["10"],prob_list11=prob_list["11"],prob_list12=prob_list["12"],prob_list13=prob_list["13"],prob_list14=prob_list["14"],prob_list15=prob_list["15"],prob_list16=prob_list["16"],lecture_no=lecture_no,user_perm=user_info["user_perm"],user_info=user_info,user_no=user_info["user_no"]))

class Prob_add(Resource):
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
        as_list,audio_list=mod_assignment_listing(lecture_no,as_no)
        user_info=get_jwt_identity()
        return make_response(render_template("prob_mod.html",lecture_no=lecture_no,as_no=as_no,as_list=as_list,audio_list=audio_list,user_info=user_info))
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
            return{"msg" : "assignment delete success"},200
        else:
            return{"msg": "access denied"}

class Prob_submit(Resource):
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
            return make_response(render_template("prob_submit2.html",as_no=as_no,lecture_no=lecture_no,as_info=as_info,user_info=user_info))
        wav_url=get_wav_url(as_no)
        return make_response(render_template("prob_submit.html",wav_url=wav_url,as_no=as_no,lecture_no=lecture_no,as_info=as_info,user_info=user_info))
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
        else:
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
        parser.add_argument('user_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        user_no = args['user_no']
        user_info=get_jwt_identity()
        as_name=get_as_name(as_no)
        wav_url,uuid=get_prob_wav_url(as_no,user_no,lecture_no)
        if(wav_url==None):
            flash("과제 제출을 해주세요")
            return redirect(host_url + url_for('prob', lecture_no=lecture_no))
        wav_url_example=get_wav_url(as_no)
        stt_result,stt_feedback=get_stt_result(uuid)
        if(stt_result==None):
            flash("stt 작업중입니다. 잠시 후에 접속해주세요")
            return redirect(host_url + url_for('prob', lecture_no=lecture_no))
        original_stt_result=get_original_stt_result(wav_url_example)
        as_info=get_as_info(lecture_no,as_no)
        user_trans_result,professor_review,feedback_list=get_feedback(as_no,lecture_no,user_no)
        return make_response(render_template("prob_feedback.html",user_info=user_info,as_name=as_name,wav_url=wav_url,wav_url_example=wav_url_example,stt_result=stt_result,original_stt_result=original_stt_result,as_info=as_info,lecture_no=lecture_no,as_no=as_no,professor_review=professor_review,feedback_list=feedback_list,user_trans_result=user_trans_result,stt_feedback=stt_feedback,user_no=user_no))


    @assistant_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        parser.add_argument('professor_review', type=str)
        parser.add_argument('feedback',type=str,action='append')
        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        user_no = args['user_no']
        professor_review=args['professor_review']
        feedback=args['feedback']
        user_info=get_jwt_identity()
        set_feedback(as_no,lecture_no,professor_review,feedback,user_no)

class Prob_submit_list(Resource):
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
            return make_response(render_template("prob_submit_list.html",user_info=user_info,user_list=user_list,as_no=as_no,lecture_no=lecture_no))



ALLOWED_SOUND_EXTENSIONS = {'wav','mp3','mp4'}
def allowed_sound_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_SOUND_EXTENSIONS

class prob_upload(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()      
        parser.add_argument('prob_sound', type=FileStorage, location='files')        
        args = parser.parse_args()        
        file= args['prob_sound']

        uuid_str=str(uuid.uuid4())
        filename = uuid_str
        path = f'{os.environ["UPLOAD_PATH"]}/{filename}.' + file.filename.rsplit('.', 1)[1].lower()
        if file and allowed_sound_file(file.filename):
            #filename = secure_filename(file.filename)
            # file.save('./static/audio/{0}'.format(filename))
            file.save(path)
        
        # task = do_stt_work.delay(filename)
        res = {
            "file_path": path, #추후 파일명에대한 해쉬처리 필요
            # "job": task.id
        }
        return jsonify(res)

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
        path = f'{os.environ["UPLOAD_PATH"]}/{filename}.' + file.filename.rsplit('.', 1)[1].lower()
        if file and allowed_file(file.filename):
            file.save(path)
        else:
            return {"msg":"file upload fail"},400
        res = {
            "file_path": path, #추후 파일명에대한 해쉬처리 필요
            "file_name": file.filename
        }
        return jsonify(res)