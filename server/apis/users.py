from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)
from ..services.login_service import (
    admin_required, DeleteResult
)
from ..services.admin_service import (
    get_users_info, delete_user, init_user_limit, InitResult
)
from server import db
from ..model import User

class Users(Resource):
    @admin_required()
    def get(self):
        res=get_users_info()
        return jsonify(users_info=res)
        
    @admin_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_no', type=str, required=True, help="user_no is required")
        args = parser.parse_args()
        user_no = args['user_no']
        result = init_user_limit(user_no)
        if(result == InitResult.SUCCESS):
            return {"msg":"Init fail limit success"}, 200
        else:
            return {"msg":"INVALID USER No"}, 403

    @admin_required()
    def delete(self,user_no):
        result = delete_user(user_no)
        if(result == DeleteResult.SUCCESS):
            return {"msg": "Delete User SUCCESS"}, 200
        else:
            return {"msg": "INVALID User No"}, 403

        

