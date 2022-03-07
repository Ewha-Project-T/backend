from flask import jsonify
from flask_restful import reqparse, Resource
from flasgger import swag_from
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity, create_refresh_token,get_jwt
)
import re
from ..services.login_service import login, LoginResult

jwt_blocklist = set() #로그아웃 사용

class Login(Resource):
    @swag_from("../../docs/login/get.yml")
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        return jsonify(user_id=current_user)
        
    # login
    @swag_from("../../docs/login/post.yml")
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        args = parser.parse_args()
        user_id = args['id']
        user_pw = args['pw']
        result, account = login(user_id, user_pw) # 계정정보 리턴
        if(result==LoginResult.SUCCESS):
            access_token=create_access_token(identity=user_id)
            refresh_token=create_refresh_token(identity=user_id)
            return jsonify(
                access_token=access_token,
                refresh_token=refresh_token
            )
        else:
            return {"msg":"Bad username or password"}, 401

    # register
    @swag_from("../../docs/login/put.yml")
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        parser.add_argument('email', type=str, required=True, help="Email is required")
        args = parser.parse_args()
        user_id = args['id']
        user_pw = args['pw']
        user_email = args['email']
        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            #db에서 입력값이랑 겹치는거있는지 체크
            if len(user_pw)<4 or len(user_pw)>20:#비밀번호 길이 제한
                return {
                    "error" : "Invaild password"
                }, 400
            else:
                #user_pw 해쉬 암호화 추가해야됨
                #DB에 저장및 토큰발급
                access_token=create_access_token(identity=user_id)
                return jsonify(
                    access_token=access_token
                )
        else:
            return {
                "error": "Invalid Email"
            }, 400

    # logout
    @jwt_required()
    def delete(self):
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti) #redis,db를 이용하면 좋겠지만 시간이 늘어남
        return jsonify(msg="Access token revoked")

    



      
