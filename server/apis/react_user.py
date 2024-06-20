from flask import jsonify
from flask_restful import Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
from ..services.user_service import get_user_by_id

#유저 정보를 받아오는 API
class User(Resource):
    @jwt_required()
    def get(self):
        #유저 정보를 받아오는 함수
        user_info=get_jwt_identity()
        res = get_user_by_id(user_info["user_no"])
        return jsonify(res)
