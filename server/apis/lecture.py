from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.lecture_service import lecture_listing, make_lecture,modify_lecture,delete_lecture
from ..services.login_service import (
     admin_required, professor_required, assistant_required
)


class Lecture(Resource):

    def get(self):#강의목록
        lecture_list = lecture_listing()
        return jsonify(lecture_list=lecture_list)

    def post(self):#강의생성/교수이상의권한
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help="Nameis required")
        parser.add_argument('year', type=str, required=True, help="Year is required")
        parser.add_argument('semester', type=str, required=True, help="Semester is required")
        parser.add_argument('major', type=str, required=True, help="Major is required")
        parser.add_argument('separated', type=str, required=True, help="separated id is required")
        parser.add_argument('professor', type=str, required=True, help="professor is required")

        args = parser.parse_args()
        lecture_name = args['name']
        lecture_year = args['year']
        lecture_semester = args['semester']
        lecture_major=args['major']
        lecture_separated= args['separated']
        lecture_professor = args['professor']
        make_lecture(lecture_name,lecture_year,lecture_semester,lecture_major,lecture_separated,lecture_professor)#추후 에러코드관리
        return{"msg" : "lecture make success"},201

    def patch(self):#강의수정권한관리 만든사람, 관리자
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        parser.add_argument('name', type=str, required=True, help="Nameis required")
        parser.add_argument('year', type=str, required=True, help="Year is required")
        parser.add_argument('semester', type=str, required=True, help="Semester is required")
        parser.add_argument('major', type=str, required=True, help="Major is required")
        parser.add_argument('separated', type=str, required=True, help="separated id is required")
        parser.add_argument('professor', type=str, required=True, help="professor is required")

        args = parser.parse_args()
        lecture_no = args['lecture_no']
        lecture_name = args['name']
        lecture_year = args['year']
        lecture_semester = args['semester']
        lecture_major=args['major']
        lecture_separated= args['separated']
        lecture_professor = args['professor']
        modify_lecture(lecture_no,lecture_name,lecture_year,lecture_semester,lecture_major,lecture_separated,lecture_professor)#추후 에러코드관리
        return{"msg" : "lecture modify success"},200

    def delete(self):#강의삭제/권한관리 만든사람, 관리자
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True, help="lecture_no is required")
        args = parser.parse_args()
        lecture_no = args['lecture_no']
        delete_lecture(lecture_no)
        return{"msg" : "lecture delete success"},200