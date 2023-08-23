from flask import jsonify, make_response, render_template, request, redirect, url_for,abort,flash
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt,set_access_cookies,set_refresh_cookies,unset_jwt_cookies
)
import re
from ..services.mail_service import (
    gen_verify_email_code,get_access_code,access_check_success,signup_email_validate
)
import uuid,hashlib
from os import environ as env
host_url=env["HOST"]

class Email(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str)
        args = parser.parse_args()
        user_email = args['email']
        if(get_access_code(user_email)==0):
            signup_email_validate(user_email,gen_verify_email_code(user_email))
            msg="인증코드가 발급되었습니다.\n이메일 인증을 완료해 주세요."
        else:
            msg="이메일 인증이 필요합니다.\n가입하신 이메일에서 확인해주세요."
        return redirect(host_url+ url_for('login',msg=msg))
    def post(self):#react용 이메일
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str)
        args = parser.parse_args()
        user_email = args['email']
        msg=""
        if(get_access_code(user_email)==0):
            signup_email_validate(user_email,gen_verify_email_code(user_email))
            msg="인증코드가 발급되었습니다.\n이메일 인증을 완료해 주세요."
        else:
            msg="이메일 인증이 필요합니다.\n가입하신 이메일에서 확인해주세요."
        return jsonify({"location":"/login", "msg":msg,"emailcheckSuccess" : 1})
class Verify_email(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str)
        parser.add_argument('code', type=str)
        args = parser.parse_args()
        email = args['email']
        code = args['code']
        s_code = get_access_code(email)
        if(s_code==0):
            msg="인증코드가 만료 되었습니다.\n로그인을 진행해 인증코드를 새로 발급 받아주세요"
            return redirect(host_url+ url_for('login',msg=msg))
        if code == s_code:
            msg="인증 되었습니다."
            access_check_success(email)
            return redirect(host_url+ url_for('login',msg=msg))
        else:
            msg="인증코드가 유효하지 않습니다."
            return redirect(host_url+ url_for('login',msg=msg))
    