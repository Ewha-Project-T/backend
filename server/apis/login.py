from flask import jsonify, make_response, render_template, request, redirect, url_for,abort
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt,set_access_cookies,set_refresh_cookies
)
import re
from ..services.login_service import (
    login, register, LoginResult, RegisterResult, create_tokens, admin_required, professor_required, assistant_required,real_time_email_check
)

from os import environ as env
host_url=env["HOST"]
jwt_blocklist = set()
perm_list={"학생":1,"조교":2,"교수":3}

class Login(Resource): 
    def get(self):
        msg = ""
        if request.args.get('msg') != "":
            msg = request.args.get('msg')
        return make_response(render_template('login.html',msg=msg))
    def post(self):#로그인
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, help="EMAIL is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        args = parser.parse_args()
        user_email = args['email']
        user_pw = args['pw']
        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):#나중에 ewha.ac.kr같은 것만 되게 수정해야됨
            result, account = login(user_email, user_pw)
            if(result==LoginResult.ACC_IS_NOT_FOUND):
                msg="User Not Found"
                return redirect(host_url + url_for('login', msg=msg))
            if(result==LoginResult.NEED_ADMIN_CHECK):
                msg="you need admin check"
                return redirect(host_url + url_for('login', msg=msg))
            if(result==LoginResult.LOGIN_COUNT_EXCEEDED):
                msg="clogin count exceeded"
                return redirect(host_url + url_for('login', msg=msg))
            if(result==LoginResult.SUCCESS):
                msg=""
                access_token, refresh_token = create_tokens(account)
                if(account.permission==0):
                    res=make_response(redirect(host_url+url_for('admin')))
                    set_access_cookies(res,access_token)
                    set_refresh_cookies(res,refresh_token)
                    return res
                else:
                    res=make_response(redirect(host_url+url_for('lecture')))
                    set_access_cookies(res,access_token)
                    set_refresh_cookies(res,refresh_token)
                    return res
    

            msg="invalid password"
            return redirect(host_url + url_for('login', msg=msg))
        else:
            msg="check email"
            return redirect(host_url + url_for('login', msg=msg))
    @jwt_required()
    def delete(self):#로그아웃
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti)
        return jsonify(msg="Access token revoked")

class Join(Resource):
    def get(self):
        msg = ""
        if request.args.get('msg') == "":
            msg = request.args.get('msg')
        parser = reqparse.RequestParser()
        parser.add_argument('mode', type=str)
        parser.add_argument('email', type=str)
        args=parser.parse_args()
        mode=args['mode']
        email=args['email']
        if(mode == "emailChk"):
            result=real_time_email_check(email)
            if(result==1):
                return {"msg":"email_exist"}
        
        return make_response(render_template('join.html',msg=msg))

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help="Email is required")
        parser.add_argument('pw', type=str, help="PW is required")
        parser.add_argument('pw2', type=str, help="PW2 is required")
        parser.add_argument('name', type=str, help="name is required")
        parser.add_argument('major', type=str, help="major id is required")
        parser.add_argument('perm', type=str, help="Permission is required")

        args = parser.parse_args()
        user_email = args['email']
        user_pw = args['pw']
        user_pw2 = args['pw2'] 
        user_name=args['name']
        user_major= args['major']
        if args['perm'] not in perm_list:
            user_perm=1
        else:
            user_perm=perm_list[args['perm']]

        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            result=register(user_email,user_pw,user_name,user_major, user_perm)
            if(result==RegisterResult.SUCCESS):
                msg="register success"
                return redirect(host_url+ url_for('login'))

            elif(result==RegisterResult.USEREMAIL_EXIST):
                msg="user email exist"
                return redirect(host_url + url_for('join', msg=msg))

            elif(result==RegisterResult.INVALID_PERM):
                msg="invalid permission"
                return redirect(host_url + url_for('join', msg=msg))

            else:
                msg="bad parameters"
                return redirect(host_url + url_for('join', msg=msg))
#
        else:
            msg="invalid email"
            return redirect(host_url + url_for('join', msg=msg))

class Email_check(Resource):
    def get(self):
        return make_response(render_template('mail_check.html'))

	
class LoginRefresh(Resource):#리프래쉬 토큰
    @jwt_required(refresh=True)
    def get(self):
        current_user = get_jwt_identity()
        if(current_user==None):
            res=make_response(redirect(host_url+url_for('login')))
            return res
        new_access_token = create_access_token(identity=current_user, fresh=False)
        res=make_response(redirect(host_url+url_for('lecture')))
        set_access_cookies(res,new_access_token)
        return res


      
