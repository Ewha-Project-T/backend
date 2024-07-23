from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)
from ..services.user_service import get_user_by_id, update_user

#유저 정보를 받아오는 API
class User(Resource):
    @jwt_required()
    def get(self):
        #유저 정보를 받아오는 함수
        user_info=get_jwt_identity()
        res = get_user_by_id(user_info["user_no"])
        return jsonify(res)
    @jwt_required()
    def put(self):
        user_info=get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='name', required=True)
        parser.add_argument('major', type=str, help='major', required=True)

        args = parser.parse_args()
        user_name = args['name']
        user_major = args['major']
        res = update_user(user_info["user_no"],user_name,user_major)
        return jsonify(res)
