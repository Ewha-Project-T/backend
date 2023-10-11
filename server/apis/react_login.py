from flask import jsonify, make_response, render_template, request, redirect, url_for,abort
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt,set_access_cookies,set_refresh_cookies,unset_jwt_cookies
)
import re
from ..services.login_service import (
    login, register, LoginResult, RegisterResult, create_tokens, admin_required, professor_required, assistant_required,real_time_email_check,findpassword_email_check,findpassword_code_check,change_pass
)
from ..services.mail_service import (
    gen_verify_email_code,get_access_code,access_check_success,signup_email_validate
)

from os import environ as env
host_url=env["HOST"]
jwt_blocklist = set()
perm_list={"학생":1,"조교":2,"교수":3}


class Login2(Resource): 
    def get(self):
        return jsonify({"msg":"loginpage"})
    
    def post(self):#로그인
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, help="EMAIL is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        args = parser.parse_args()
        user_email = args['email']
        user_pw = args['pw']
        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            result, account = login(user_email, user_pw)
            if(result==LoginResult.ACC_IS_NOT_FOUND):
                msg="아이디와 비밀번호를 확인해주세요."
                return jsonify({ "registerSuccess" : 0,"msg":msg})
            if(result==LoginResult.NEED_EMAIL_CHECK):
                msg="가입된 이메일에서 확인바랍니다."
                return jsonify({ "registerSuccess" : 0,"msg":msg,'location':"/email", "email":user_email})
            if(result==LoginResult.LOGIN_COUNT_EXCEEDED):
                msg="로그인 시도횟수초과 관리자에게 연락바랍니다."
                return jsonify({ "registerSuccess" : 0,"msg":msg})
            if(result==LoginResult.NEED_ADMIN_CHECK):
                msg="관리자의 승인이 필요합니다."
                return jsonify({ "registerSuccess" : 0,"msg":msg})
            if(result==LoginResult.SUCCESS):
                msg=""
                access_token, refresh_token = create_tokens(account)
                if(account.permission==0):
                    resq = make_response({'loginSuccess': 1,'location':'/admin'})#location 추후 수정
                    resq.set_cookie('access_token_cookie',access_token,secure=True, httponly=True, samesite='None')          
                    return resq
                else:
                    resq = make_response({'loginSuccess': 1})
                    resq.set_cookie('access_token_cookie',access_token,secure=True, httponly=True, samesite='None')         
                    return resq
            msg="아이디와 비밀번호를 확인해주세요."
            return jsonify({ "registerSuccess" : 0,"msg":msg})
        else:
            msg="아이디와 비밀번호를 확인해주세요."
            return jsonify({ "registerSuccess" : 0,"msg":msg})
class CheckToken(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        if(current_user==None):
            return {"isAuth": 0},400
        if(current_user["user_perm"]==0):
            return {   "email": current_user["user_email"],
                       "name": current_user["user_name"],
                       "role": current_user["user_perm"],
                       "user_no": current_user["user_no"],
                       "isAuth": 1,
                       "isAdmin": 1},200
        else:
            return {   "email": current_user["user_email"],
                       "name": current_user["user_name"],
                       "role": current_user["user_perm"],
                       "user_no": current_user["user_no"],
                       "isAuth": 1,
                       "isAdmin": 0},200
                    
        
class Logout2(Resource):

    @jwt_required()
    def get(self):#로그아웃
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti)
        resq = make_response({'logoutSuccess': "true",})
        resq.set_cookie('access_token_cookie', '', expires=0, secure=True, httponly=True, samesite='None')
        return resq
        


class Join2(Resource):
    def get(self):
        return jsonify({"msg":"joinpage"})

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help="Email is required")
        parser.add_argument('pw', type=str, help="PW is required")
        parser.add_argument('pw2', type=str, help="PW2 is required")
        parser.add_argument('name', type=str, help="name is required")
        parser.add_argument('major', type=str, help="major id is required")
        parser.add_argument('perm', type=str, help="Permission is required")
        #parser.add_argument('ident', type=str, help="identify is required")

        args = parser.parse_args()
        user_email = args['email']
        user_pw = args['pw']
        user_pw2 = args['pw2'] 
        user_name=args['name']
        user_major= args['major']
        #user_ident=args['ident']
        if args['perm'] not in perm_list:
            user_perm=1
        else:
            user_perm=perm_list[args['perm']]

        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            result=register(user_email,user_pw,user_name,user_major, user_perm)#,user_ident)
            if(result==RegisterResult.SUCCESS):
                msg="register success"
                return jsonify({ "registerSuccess" : 1,"msg":msg})

            elif(result==RegisterResult.USEREMAIL_EXIST):
                msg="user email exist"
                return jsonify({ "registerSuccess" : 0,"msg":msg})

            elif(result==RegisterResult.INVALID_PERM):
                msg="invalid permission"
                return jsonify({ "registerSuccess" : 0,"msg":msg})

            else:
                msg="bad parameters"
                return jsonify({ "registerSuccess" : 0,"msg":msg})
        else:
            msg="invalid email"
            return jsonify({ "registerSuccess" : 0,"msg":msg})
	

class FindPassword(Resource):
    def get(self):
        return jsonify({"msg":"findpassword page"})
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help="Email is required")
        parser.add_argument('name', type=str, help="name is required")
        parser.add_argument('major', type=str, help="major id is required")

        args = parser.parse_args()
        user_email = args['email']
        user_name=args['name']
        user_major= args['major']

        if(findpassword_email_check(user_email,user_name,user_major)):
            signup_email_validate(user_email,gen_verify_email_code(user_email),"findpass_check")#email, code, func->url/[func] 추후현식이 경로로 바꾸기 [func]부분

            msg="email send success"
            return jsonify({ "Success" : 1,"msg":msg})
        msg="invalid email"
        return jsonify({"Success": 0, "msg":msg})
    
class FindPassword_Check(Resource):
    def get(self):
        return jsonify({"msg":"findpassword page"})
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help="Email is required")
        parser.add_argument('code', type=str, help="code is required")
        parser.add_argument('password', type=str, help="password id is required")

        args = parser.parse_args()
        email = args['email']
        code=args['code']
        password= args['password']
        if(findpassword_code_check(email,code)):
            change_pass(email,password)
            msg="password change success"
            return jsonify({"Success": 1, "msg":msg})
        msg="invalid code"
        return jsonify({"Success": 0, "msg":msg})

