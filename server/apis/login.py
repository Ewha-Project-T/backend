from flask_restful import reqparse, Resource
from flasgger import swag_from
import re

class Login(Resource):
    def get(self):
        """
        Login GET
        ---
        tags:
          - Login APIs
        responses:
          200:
            description: Login Success
        """
        return {
            "status": "success"
        }, 200
    
    # login
    def post(self):
        """
        Login with Account
        ---
        tags:
          - Login APIs
        parameters:
          - in: body
            name: user_id
            type: string
            required: true
          - in: body
            name: user_pw
            type: string
            required: true
        responses:
          200:
            description: Login Success
            schema:
              id: Success
              properties:
                status:
                  type: string
                  description: success
                  default: success
          401:
            description: User Not Found
            schema:
              id: User Not Found
              properties:
                status:
                  type: string
                  description: User Not Found
                  default: user not found
        """
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
    def put(self):
        """
        Register New Account
        ---
        tags:
          - Login APIs
        parameters:
          - in: body
            name: user_id
            type: string
            required: true
          - in: body
            name: user_pw
            type: string
            required: true
          - in: email
            name: email
            required: true
        responses:
          200:
            description: Register Success
            schema:
              id: Success
        """
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
    