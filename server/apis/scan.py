from flask import jsonify
from flask_restful import reqparse, Resource
from ..services.login_service import login_required

class Scan(Resource):
    @login_required()
    def get(self):
        return {"msg":"scanAPI"}, 200

    @login_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="FileName is required")
        args = parser.parse_args()
        filename = args['file_name']
        return {"msg":filename}, 200
