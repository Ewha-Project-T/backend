from flask import jsonify, make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required

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
        print(filename)
        response = make_response(filename)
        response.headers['Content-Type'] = 'text/json'
        response.headers['Content-Disposition'] = 'attachment; filename=selected_items.json'
        return response, 200

