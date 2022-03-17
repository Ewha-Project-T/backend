from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)
from ..services.login_service import (
    admin_required
)
from server import db
from ..model import User

def get_users_info():
    acc_list = User.query.all()
    info_list = []
    for info in acc_list:
        tmp_info = {}
        tmp_info["project_no"] = info.project_no
        tmp_info["user_no"] = info.user_no
        tmp_info["id"] = info.id
        tmp_info["permission"] = info.permission
        tmp_info["name"] = info.name
        tmp_info["email"] = info.email
        tmp_info["login_fail"] = info.login_fail_limit
        info_list.append(tmp_info)
    return info_list

class Users(Resource):
    @admin_required()
    def get(self):
        res=get_users_info()
        return jsonify(users_info=res)
