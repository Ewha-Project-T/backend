from flask import jsonify, make_response, render_template, request, redirect, url_for
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.login_service import (
    login, register, LoginResult, RegisterResult, create_tokens, admin_required, professor_required, assistant_required
)

jwt_blocklist = set()

class Login(Resource): 
    def get(self):
        return make_response(render_template('login.html'))
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
                return {"msg":"User Not Found"}, 403
            if(result==LoginResult.NEED_ADMIN_CHECK):
                return {"msg":"you need Admin check"},403
            if(result==LoginResult.LOGIN_COUNT_EXCEEDED):
                return {"msg":"login count exceeded"}, 403
            if(result==LoginResult.SUCCESS):
                access_token, refresh_token = create_tokens(account)
                if(account.permission==0):
                    return {
                        'access_token' : access_token,
                        'refresh_token' : refresh_token
                    }, 201, {'location':'/adminpage'}
                else:
                    return {
                        'access_token' : access_token,
                        'refresh_token': refresh_token
                    }, 201, {'location':'/'}
  
    @jwt_required()
    def delete(self):#로그아웃
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti)
        return jsonify(msg="Access token revoked")

msg=""
class Join(Resource):
    def get(self):
        return make_response(render_template('join.html',msg=msg))

    def post(self):
        msg=""
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, help="Email is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        parser.add_argument('pw2', type=str, required=True, help="PW2 is required")
        parser.add_argument('name', type=str, required=True, help="name is required")
        parser.add_argument('major', type=str, required=True, help="major id is required")
        parser.add_argument('perm', type=int, required=True, help="Permission is required")
        args = parser.parse_args()
        return "AFAF"
        user_email = args['email']
        user_pw = args['pw']
        user_pw2 = args['pw2']
        user_name=args['name']
        user_major= args['major']
        user_perm = args['perm']
        '''
        user_email = request.form['email']
        user_pw = request.form['pw']
        user_pw2 = request.form['pw2']
        user_name = request.form['name']
        user_major = request.form['major']
        user_perm = request.form['perm']

        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            result=register(user_email,user_pw,user_name,user_major, user_perm)
            #result = 'asdf'
            if(result==RegisterResult.SUCCESS):
                msg="register success"
                return redirect(url_for('login'))
#                return{'location':'/login'},201
            elif(result==RegisterResult.USEREMAIL_EXIST):
                msg="user email exist"
                return {'location':'/join'},400
            elif(result==RegisterResult.INVALID_PERM):
                msg="invalid permission"
                return {'location':'/join'},400
            else:
                msg="bad parameters"
                return redirect('https://ewha.ltra.cc' + url_for('join', msg=msg))
#                return {'location':'/join'},404
        else:
            msg="invalid email"
            return {'location':'/join'},400


	


class LoginRefresh(Resource):#리프래쉬 토큰
    @jwt_required(refresh=True)
    def get(self):
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_access_token}, 200
    



      
