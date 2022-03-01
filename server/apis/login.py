from flask_restful import reqparse, Resource
from flasgger import swag_from
import re

class Login(Resource):
    @swag_from("../../docs/login/get.yml")
    def get(self):
        return {
            "status": "success"
        }, 200
    # login
    @swag_from("../../docs/login/post.yml")
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        args = parser.parse_args()

        user_id = args['id']
        user_pw = args['pw']
        if(user_id=='guest' and user_pw=='guest'):
            return {
                "status": "success"
            }, 200
        else:
            return {
                'error': 'user not found'
            }, 401
    
    # registerr
    @swag_from("../../docs/login/put.yml")
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True, help="ID is required")
        parser.add_argument('pw', type=str, required=True, help="PW is required")
        parser.add_argument('email', type=str, required=True, help="Email is required")
        args = parser.parse_args()
        user_id = args['id']
        user_pw = args['pw']
        user_email = args['email']
        if re.match("^[A-Za-z0-9]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[A-Za-z0-9])*\.[A-Za-z]{2,3}$", user_email):
            return {
                "status": "success"
            }, 200
        else:
            return {
                "error": "Invalid Email"
            }, 400

    # delete account
    def delete(self):
        # 계정삭제 로직
        return {
            "status": "Delete account success"
        }, 200
    