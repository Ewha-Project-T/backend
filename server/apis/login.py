from flask import jsonify
from flask_restful import reqparse, Resource
from flasgger import swag_from
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.login_service import (
    login, register, delete, LoginResult, RegisterResult, create_tokens, 
    DeleteResult, change, ChangeResult, admin_required
)

jwt_blocklist = set()

class Login(Resource):
    @swag_from("../../docs/login/get.yml")
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        return jsonify(user_account=current_user)

    @swag_from("../../docs/login/post.yml")
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        args = parser.parse_args()
        user_id = args['id']
        user_pw = args['pw']
        result, account = login(user_id, user_pw)
        if(result==LoginResult.LOGIN_COUNT_EXCEEDED):
            return {"msg":"LOGIN_COUNT_EXCEEDED"}, 400
        if(result==LoginResult.SUCCESS):
            access_token, refresh_token = create_tokens(account)
            return jsonify(
                access_token = access_token,
                refresh_token = refresh_token
            )
        else:
            return {"msg":"Bad username or password"}, 403

    @swag_from("../../docs/login/put.yml")
    @admin_required()
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        parser.add_argument('name', type=str, required=True, help="name is required")
        parser.add_argument('email', type=str, required=True, help="Email is required")
        parser.add_argument('pro_id', type=str, required=True, help="Project id is required")
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
                return{
                    "msg" : "success"
                },200
            elif(result==RegisterResult.INVALID_IDPW):
                return{
                    "error" : "invalid ID or PW"
                },403
            elif(result==RegisterResult.USERID_EXIST):
                return{
                    "error" : "user id exist"
                },403
            elif(result==RegisterResult.USEREMAIL_EXIST):
                return{
                    "error" : "user email exist"
                },403
            elif(result==RegisterResult.INVALID_PERM):
                return {
                    "error" : "invalid permission"
                }, 403
            elif(result==RegisterResult.INVALID_PROJECT):
                return {
                    "error" : "invalid project"
                }, 403
            else:
                return{
                    "error" : "internal error"
                },405
        else:
            return {
                "error": "Invalid Email"
            }, 403

    @jwt_required()
    def patch(self):
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
            return {'msg':'Incorrect old password'}, 403
        elif(res==ChangeResult.INVALID_PW):
            return {'msg':'Invalid password'}, 403
        elif(res==ChangeResult.INVALID_EMAIL):
            return {'msg':'Invalid email'}, 403
        elif(res==ChangeResult.INVALID_NAME):
            return {'msg':'Invalid name'}, 403
        elif(res==ChangeResult.DUPLICATED_EMAIL):
            return {'msg':'Duplicated EMAIL'}, 403
        else:
            return {'msg':'Internal Error'}, 405

    @jwt_required()
    def delete(self):
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti)
        return jsonify(msg="Access token revoked")

class Account(Resource):
    @swag_from("../../docs/Account/delete.yml")
    @jwt_required()
    def delete(self):
        current_user=get_jwt_identity()
        result=delete(current_user["user_id"])
        if(result==DeleteResult.SUCCESS):
            return{
                "msg":"success"
            },200
        else:
            return{
                "error": "delete account fail"
            },403

class LoginRefresh(Resource):
    @jwt_required(refresh=True)
    def get(self):
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user, fresh=False)
        return {
            "access_token": new_access_token
        }, 200
    
class Admin(Resource):
    @admin_required()
    def get(self):
        current_admin = get_jwt_identity()
        if(current_admin["user_perm"]==2):
            return {"msg":"admin authenticated"}, 200
        return {"msg": "you're not admin"}, 403




      
