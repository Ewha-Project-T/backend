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
    return acc_list

class Users(Resource):
    @admin_required()
    def get(self):
        res=get_users_info()
        for info in res:
            print(info)
        return {"msg":"Users info API"}, 200
