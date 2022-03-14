from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
from ..services.project_service import (
    create_project
)
class Project(Resource):
    @jwt_required()
    def get(self):
        return {"msg":"Project API"}, 200

    #@jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('prj_name', type=str, required=True, help="Project Name is required")
        parser.add_argument('prj_start', type=str, required=True, help="Start Date required")
        parser.add_argument('prj_end', type=str, required=True, help="End Date is required")
        args = parser.parse_args()
        prj_name = args['prj_name']
        prj_start = args['prj_start']
        prj_end = args['prj_end']
        create_project(prj_name,prj_start,prj_end)
        return {"msg":"success"},200