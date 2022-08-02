from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.login_service import (
    login, register, delete, LoginResult, RegisterResult, create_tokens, 
    DeleteResult, change, ChangeResult, admin_required, professor_required, assistant_required
)
from ..services.admin_service import patch_user, UserChangeResult

jwt_blocklist = set()

class Login(Resource): #로그인
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        return jsonify(user_account=current_user)

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        args = parser.parse_args()
        user_id = args['id']
        user_pw = args['pw']
        result, account = login(user_id, user_pw)
        if(result==LoginResult.ACC_IS_NOT_FOUND):
            return {"msg":"User Not Found"}, 403
        if(result==LoginResult.LOGIN_COUNT_EXCEEDED):
            return {"msg":"login count exceeded"}, 403
        if(result==LoginResult.SUCCESS):
            access_token, refresh_token = create_tokens(account)
            if(account.permission==2):
                return {
                    'access_token' : access_token,
                    'refresh_token' : refresh_token
                }, 201, {'location':'/adminpage'}
            else:
                return {
                    'access_token' : access_token,
                    'refresh_token': refresh_token
                }, 201, {'location':'/'}
        else:
            return {"msg":"Bad username or password"}, 400

    @jwt_required()
    def put(self):#회원가입
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        parser.add_argument('name', type=str, required=True, help="name is required")
        parser.add_argument('email', type=str, required=True, help="Email is required")
        parser.add_argument('pro_id', type=str, required=True, help="Project id is required")
        parser.add_argument('perm', type=int, required=True, help="Permission is required")
        args = parser.parse_args()
        user_id = args['id']
        user_pw = args['pw']
        user_name=args['name']
        user_email = args['email']
        user_project= args['pro_id']
        user_perm = args['perm']
        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            result=register(user_id,user_pw,user_name,user_email, user_project, user_perm)
            if(result==RegisterResult.SUCCESS):
                return{"msg" : "register success"},201
            elif(result==RegisterResult.INVALID_IDPW):
                return{"msg" : "invalid id or pw"},400
            elif(result==RegisterResult.USERID_EXIST):
                return{"msg" : "user id exist"},400
            elif(result==RegisterResult.USEREMAIL_EXIST):
                return{"msg" : "user email exist"},400
            elif(result==RegisterResult.INVALID_PERM):
                return {"msg" : "invalid permission"}, 400
            elif(result==RegisterResult.INVALID_PROJECT):
                return {"msg" : "invalid project"}, 400
            else:
                return{"msg" : "bad parameters"},404
        else:
            return {"msg": "Invalid Email"}, 400

    @jwt_required()
    def patch(self):#회원수정
        parser = reqparse.RequestParser()
        parser.add_argument('old_pw', type=str)
        parser.add_argument('new_pw', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('name', type=str)
        args = parser.parse_args()
        old_pw = args['old_pw']
        new_pw = args['new_pw']
        email = args['email']
        name = args['name']
        res = change(old_pw, new_pw, name, email)
        if(res==ChangeResult.SUCCESS):
            return {'msg':'success'},200
        elif(res==ChangeResult.INCORRECT_PW):
            return {'msg':'Incorrect old password'}, 400
        elif(res==ChangeResult.INVALID_PW):
            return {'msg':'Invalid password'}, 400
        elif(res==ChangeResult.INVALID_EMAIL):
            return {'msg':'Invalid email'}, 400
        elif(res==ChangeResult.INVALID_NAME):
            return {'msg':'Invalid name'}, 400
        elif(res==ChangeResult.DUPLICATED_EMAIL):
            return {'msg':'Duplicated EMAIL'}, 400
        else:
            return {'msg':'Internal Error'}, 400

    @jwt_required()
    def delete(self):#로그아웃
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti)
        return jsonify(msg="Access token revoked")

class Account(Resource):
    @jwt_required()
    def delete(self):#계정삭제
        current_user=get_jwt_identity()
        result=delete(current_user["user_id"])
        if(result==DeleteResult.SUCCESS):
            return{"msg":"success"},200
        else:
            return{"msg": "invalid user id"},400

class LoginRefresh(Resource):#리프래쉬 토큰
    @jwt_required(refresh=True)
    def get(self):
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_access_token}, 200
    
class Admin(Resource):
    @admin_required()
    def get(self):#관리자체크
        current_admin = get_jwt_identity()
        if(current_admin["user_perm"]==2):
            return {"msg":"admin authenticated"}, 200
        return {"msg": "you're not admin"}, 403
    @admin_required()
    def patch(self):#관리자가 계정생성
        cur_user = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('user_no', type=int, required=True)
        parser.add_argument('new_pw', type=str)
        if(cur_user["user_perm"] == 2):
            parser.add_argument('new_id', type=str)
            parser.add_argument('email', type=str)
            parser.add_argument('name', type=str)
        args = parser.parse_args()
        user_no = args['user_no']
        new_pw = args['new_pw']
        if(cur_user["user_perm"] == 2):
            new_id = args['new_id']
            email = args['email']
            name = args['name']
        else:
            new_id = None
            email = None
            name = None
        result = patch_user(user_no,new_id,new_pw,email,name)
        if(result == UserChangeResult.DUPLICATED_EMAIL):
            return {"msg":"duplicated email"}, 403
        elif(result == UserChangeResult.DUPLICATED_ID):
            return {"msg":"duplicated id"}, 403
        elif(result == UserChangeResult.INVALID_USER):
            return {"msg": "Invalid User"}, 403
        else:
            return {"msg":"success"}, 200






      
