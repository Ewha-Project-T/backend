from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.admin_service import user_listing, activating_user,AdminResult
from os import environ as env
host_url=env["HOST"]
class admin(Resource):
    @jwt_required()
    def get(self):#계정전체 명단
        result,user_list = user_listing()
        if(result==AdminResult.NOT_FOUND):
            return {"msg":"none user"},404
        return jsonify(uesr_list=user_list)
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email',type=str, required=True, help="email is required")
        args= parser.parse_args()
        email= args['email']
        activating_user(email)
        return {"msg":"Activating account"},200

    def put(self):#일단 put에 넣음 활성화 필요한 계정명단
        result,user_list = user_listing(1)
        if(result==AdminResult.NOT_FOUND):
            return {"msg":"none user"},404
        return jsonify(uesr_list=user_list)
