from flask import jsonify, make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
import werkzeug

class ScriptAPI(Resource):
    @jwt_required()
    def get(self):
        return {"msg":"scriptAPI"}, 200

    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="FileName is required")
        args = parser.parse_args()
        filename = args['file_name']
        headers = {}
        headers['Content-Type'] = 'text/json'
        headers['Content-Disposition'] = 'attachment; filename=selected_items.json'
        return {"msg": filename}, 200, headers

    @jwt_required()
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=werkzeug.datastructures.FileStorage, location='files')
        args = parser.parse_args()
        file_object = args['file_name']
        print(file_object)
        file_object.save("test.txt")
        return {"msg":"good"}, 200

