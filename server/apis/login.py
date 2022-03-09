from flask import jsonify
from flask_restful import reqparse, Resource
from flasgger import swag_from
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity, create_refresh_token,get_jwt
)
import re
from ..services.login_service import login,register,delete,LoginResult,RegisterResult,DeleteResult

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
        parser.add_argument('name', type=str, required=True, help="name is required")
        parser.add_argument('email', type=str, required=True, help="Email is required")
        args = parser.parse_args()
        user_id = args['id']
        user_pw = args['pw']
        user_name=args['name']
        user_email = args['email']
        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            result=register(user_id,user_pw,user_name,user_email)
            if(result==RegisterResult.SUCCESS):
                access_token=create_access_token(identity=user_id)
                return{
                    "msg" : "success"
                },200
            elif(result==RegisterResult.INVALID_IDPW):
                return{
                    "error" : "invalid ID or PW"
                },400
            elif(result==RegisterResult.USERID_EXIST):
                return{
                    "error" : "user id exist"
                },400
            elif(result==RegisterResult.USEREMAIL_EXIST):
                return{
                    "error" : "user email exist"
                },400
            else:
                return{
                    "error" : "internal error"
                },400
        else:
            return {
                "error": "Invalid Email"
            }, 400

    # logout
    @jwt_required()
    def delete(self):
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti) #redis,db를 이용하면 좋겠지만 시간이 늘어남
        delete()
        return jsonify(msg="Access token revoked")

class Account(Resource):#회원탈퇴용 class
    @swag_from("../../docs/Account/delete.yml")
    @jwt_required()
    def delete(self):
        current_user=get_jwt_identity()
        result=delete(current_user)
        if(result==DeleteResult.SUCCESS):
            return{
                "msg":"success"
            },200
        else:
            return{
                "error": "Invalid Value"
            },400
    



      
