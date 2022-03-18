from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)
from ..services.login_service import (
    admin_required, DeleteResult
)
from ..services.admin_service import (
    get_users_info, delete_user
)
from server import db
from ..model import User

class Users(Resource):
    @admin_required()
    def get(self):
        res=get_users_info()
        return jsonify(users_info=res)
    @admin_required()
    def delete(self,user_no):
        result = delete_user(user_no)
        if(result == DeleteResult.SUCCESS):
            return {"msg": "Delete User SUCCESS"}, 200
        else:
            return {"msg": "INVALID User No"}, 403

        

