from flask import jsonify,render_template, request, redirect, url_for,abort,make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re

from ..services.login_service import admin_required
from ..services.admin_service import user_listing, activating_user,AdminResult,del_user
from ..services.lecture_service import lecture_listing
from os import environ as env
host_url=env["HOST"]

class Admin(Resource):
    @admin_required()
    def get(self):
        user_info=get_jwt_identity()
        result,user_list = user_listing()
        if(result==AdminResult.NOT_FOUND):
            return {"msg":"none user"},404
        return make_response(render_template("admin_list.html",user_list=user_list,user_info=user_info))
    @admin_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email',type=str, required=True, help="email is required")
        args= parser.parse_args()
        email= args['email']
        activating_user(email)
        return {"msg":"Activating account"},200


class Admin2(Resource):
    @admin_required()
    def get(self):#활성화 필요한 계정명단
        user_info=get_jwt_identity()
        result,user_list = user_listing(1)
        if(result==AdminResult.NOT_FOUND):
            return {"msg":"none user"},404
        return make_response(render_template("admin_list.html",user_list=user_list,user_info=user_info))
    @admin_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email',type=str, required=True, help="email is required")
        args= parser.parse_args()
        email=args['email']
        del_user(email)
        return {"msg":"success"}
