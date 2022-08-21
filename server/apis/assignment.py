from ast import keyword
import json
from pickle import TRUE
from flask import jsonify,render_template, request, redirect, url_for,abort,make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.assignment_service import prob_listing,make_as,mod_as,get_wav_url
from werkzeug.utils import secure_filename
from os import environ as env
from werkzeug.datastructures import FileStorage
import os

host_url=env["HOST"]
perm_list={"학생":1,"조교":2,"교수":3}

class Prob(Resource):
    def get(self):#과제리스트
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        prob_list=prob_listing(lecture_no)
        return make_response(render_template("prob_list.html",prob_list=prob_list,lecture_no=lecture_no))

class Prob_add(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        return make_response(render_template("prob_add.html",lecture_no=lecture_no))
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

        #original_text = args['original_text']
        make_as(lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,"",upload_path,prob_region)#original_text,upload_url
        return{"msg" : "success"},200

class Prob_mod(Resource):
    def get(self):
        return "hi"# 과제 생성 창이 만들어지면 assignment_no로 불러와서 값넣어줄것
    def post(self):#과제수정
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int, required=True,help="assignment_no is required")
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        parser.add_argument('week', type=str, required=True, help="week is required")
        parser.add_argument('limit_time', type=str,  required=True, help="limit_time is required")
        parser.add_argument('as_name', type=str, required=True, help="as_name is required")
        parser.add_argument('as_type', type=str, required=True, help="as_type is required")
        parser.add_argument('keyword', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('re_limit', type=str, required=True, help="re_limit is required")
        parser.add_argument('speed', type=float, required=True, help="speed is required")
        parser.add_argument('disclosure', type=int, default=0)
        parser.add_argument('original_text', type=str)
        parser.add_argument('upload_url', type=str)

        args = parser.parse_args()
        as_no=args['as_no']
        lecture_no = args['lecture_no']
        week = args['week']
        limit_time = args['limit_time']
        as_name = args['as_name']
        as_type = args['as_type']
        keyword = args['keyword']
        description = args['description']
        re_limit = args['re_limit']
        speed = args['speed']
        disclosure = args['disclosure']
        original_text = args['original_text']
        upload_url = args['upload_url']
        mod_as(as_no,lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text,upload_url)
        return{"msg" : "success"},200

class Prob_submit(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        wav_url=get_wav_url(as_no)
        wav_url=wav_url.split('/',2)[-1]
        return make_response(render_template("prob_submit.html",wav_url=wav_url))

class Prob_feedback(Resource):
    def get(self):
        return make_response(render_template("prob_feedback.html"))

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
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save('./static/audio/{0}'.format(secure_filename(file.filename)))
        res = {"file_path": f"/static/audio/{filename}"}#추후 파일명에대한 해쉬처리 필요
        return jsonify(res)