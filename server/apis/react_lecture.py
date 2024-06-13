import json
from operator import le
from datetime import datetime
from pickle import TRUE
from flask import jsonify,render_template, request, redirect, url_for,abort,make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.lecture_service import get_enrolment_code, lecture_listing, make_lecture, modify_enrolment,modify_lecture,delete_lecture, request_enrolment, search_student,major_listing,attendee_add,attendee_listing,lecture_access_check,mod_lecutre_listing
from ..services.login_service import get_all_user

from os import environ as env
host_url=env["HOST"]
perm_list={"학생":1,"조교":2,"교수":3}
class React_Lecture(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        if(user_info["user_perm"]==0):
            lecture_list=lecture_listing()
        else:
            lecture_list=lecture_listing(user_info)
        
        return {   "lecturelist":lecture_list,
                       "userInfo": user_info,
                       "role": user_info["user_perm"],
                       },200



class React_Lecture_mod_del(Resource):
    
    @jwt_required()
    def get(self):#강의삭제/권한관리 만든사람, 관리자
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        user_info=get_jwt_identity()
        if(lecture_access_check(user_info["user_no"],lecture_no) or user_info["user_perm"]==0):
            delete_lecture(lecture_no)
            return{"msg" : "lecture delete success"},200
        else:
            return{"msg": "access denied"}

class React_Student(Resource):
    @jwt_required()
    def get(self):#학생조회 이름과 전공으로 검색 후 리스팅
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('major', type=str)
        args = parser.parse_args()
        user_name=args['name']
        user_major= args['major']
        user_list = search_student(user_name,user_major)
        return {"userlist":user_list},200

        
    
class Major(Resource):
    @jwt_required()
    def get(self):#해당전공 과목 리스팅
        parser=reqparse.RequestParser()
        parser.add_argument('major',type=str)
        args=parser.parse_args()
        user_major=args['major']
        major_list= major_listing(user_major)
        return jsonify(major_list=major_list)

class Attend(Resource):
    @jwt_required()
    def get(self):# lecture no로 해당 강의의 수강생 명단 리스팅
        parser=reqparse.RequestParser()
        parser.add_argument('lecture_no',type=int)
        args=parser.parse_args()
        lecture_no=args['lecture_no']
        attendee_list=attendee_listing(lecture_no)
        return jsonify(attendee_list=attendee_list)
    @jwt_required()
    def post(self):#수강생 명단추가
        parser=reqparse.RequestParser()
        parser.add_argument('user_no',type=int)
        parser.add_argument('lecture_no',type=int)
        parser.add_argument('permission',type=str)
        args=parser.parse_args()
        user_no=args['user_no']
        lecture_no=args['lecture_no']
        permission=args['permission']
        if args['permission'] not in perm_list:
            permission=1
        else:
            permission=perm_list[args['permission']]
        attendee_add(user_no,lecture_no,permission)
        return {"msg":"add success"}

class React_Lecture_add(Resource):
    @jwt_required()
    def get(self):
        user_list=get_all_user()
        user_info=get_jwt_identity()
        now = datetime.now()
        return {   "userlist":user_list,
                       "userInfo": user_info,
                       
                       },200
    
    @jwt_required()
    def post(self):#강의생성/교수이상의권한
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_name', type=str, required=True, help="Nameis required")
        parser.add_argument('lecture_year', type=str, required=True, help="Year is required")
        parser.add_argument('lecture_semester', type=str, required=True, help="Semester is required")
        parser.add_argument('lecture_major', type=str, required=True, help="Major is required")
        parser.add_argument('lecture_separated', type=str, required=True, help="separated id is required")
        parser.add_argument('lecture_professor', type=str, required=True, help="professor is required")
        parser.add_argument('lecture_attendee', type=str, action='append', required=True)
        args = parser.parse_args()
        lecture_name = args['lecture_name']
        lecture_year = args['lecture_year']
        lecture_semester = args['lecture_semester']
        lecture_major=args['lecture_major']
        lecture_separated= args['lecture_separated']
        lecture_professor = args['lecture_professor']
        attendee=args['lecture_attendee']
        make_lecture(lecture_name,lecture_year,lecture_semester,lecture_major,lecture_separated,lecture_professor,attendee,user_info)#추후 에러코드관리
        return{"msg" : "lecture make success"},201

class React_Lecture_mod(Resource):
    @jwt_required()
    def get(self):
        user_list=get_all_user()
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int )
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        mod_list,attend_list=mod_lecutre_listing(lecture_no)
        user_info=get_jwt_identity()
        return {   "userlist":user_list,
                    "lectureNo": lecture_no,
                    "modlist" : mod_list,
                    "attendlist" : attend_list,
                    "userInfo": user_info,
                },200
    @jwt_required()
    def post(self):#강의수정권한관리 만든사람, 관리자
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int )
        parser.add_argument('lecture_name', type=str )
        parser.add_argument('lecture_year', type=str )
        parser.add_argument('lecture_semester', type=str)
        parser.add_argument('lecture_major', type=str)
        parser.add_argument('lecture_separated', type=str)
        parser.add_argument('lecture_professor', type=str)
        parser.add_argument('lecture_attendee', type=str, action='append')
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        lecture_name = args['lecture_name']
        lecture_year = args['lecture_year']
        lecture_semester = args['lecture_semester']
        lecture_major=args['lecture_major']
        lecture_separated= args['lecture_separated']
        lecture_professor = args['lecture_professor']
        attendee=args['lecture_attendee']
        if(lecture_access_check(user_info["user_no"],lecture_no) or user_info["user_perm"]==0):
            modify_lecture(lecture_no,lecture_name,lecture_year,lecture_semester,lecture_major,lecture_separated,lecture_professor,attendee,user_info)#추후 에러코드관리
            return{"msg" : "lecture modify success",
                   "lecturemodifySuccess" : 1
                   },200
        else:
            return{"msg": "access denied", "lecturemodifySuccess" : 0}

class React_Lecture_enrolment(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        user_info=get_jwt_identity()
        res = get_enrolment_code(user_info["user_no"],lecture_no)
        return jsonify(res)

    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int)
        parser.add_argument('status', type=bool)
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        status = args['status']
        user_info=get_jwt_identity()
        res = modify_enrolment(user_info["user_no"],lecture_no,status)

        return jsonify(res)

#학생 수강 신청
class React_Lecture_request(Resource):
    #학생이 수강 신청한 모든 강의 리스트
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        user_info=get_jwt_identity()
        #res = get_enrolment_list(user_info["user_no"])
        #return jsonify(res)

    #ㅎ학생이 수강 신청
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('code', type=str)
        args = parser.parse_args()
        code = args['code']
        user_info=get_jwt_identity()
        res = request_enrolment(user_info["user_no"], code)

        return jsonify(res)
