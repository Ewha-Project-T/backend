from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.lecture_service import lecture_listing
from ..services.login_service import (
     admin_required, professor_required, assistant_required
)


class Lecture(Resource):
    @jwt_required()
    def get(self):#교수 목록조회
        current_user = get_jwt_identity()
        lecture_list = lecture_listing(current_user["user_no"])
        return jsonify(lecture_list=lecture_list)

    @jwt_required()
    def post(self):#강의 작성
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help="Nameis required")
        parser.add_argument('year', type=str, required=True, help="Year is required")
        parser.add_argument('semester', type=str, required=True, help="Semester is required")
        parser.add_argument('major', type=str, required=True, help="Major is required")
        parser.add_argument('separated', type=str, required=True, help="separated id is required")
        parser.add_argument('boss', type=int, required=True, help="Boss is required")

        args = parser.parse_args()
        lecture_name = args['name']
        lecture_year = args['year']
        lecture_semester = args['semester']
        lecture_major=args['major']
        lecture_separated= args['separated']
        lecture_boss = args['boss']
        
        result=register(user_email,user_pw,user_name,user_major, user_perm)
        if(result==RegisterResult.SUCCESS):
            return{"msg" : "register success"},201
        elif(result==RegisterResult.USEREMAIL_EXIST):
            return{"msg" : "user email exist"},400
        elif(result==RegisterResult.INVALID_PERM):
            return {"msg" : "invalid permission"}, 400
        else:
            return{"msg" : "bad parameters"},404