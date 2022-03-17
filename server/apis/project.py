from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
from numpy import delete
from ..services.login_service import admin_required
from ..services.project_service import (
    create_project, delete_project,LoginResult,DeleteResult
)
class Project(Resource):
    @jwt_required()
    def get(self):
        return {"msg":"Project API"}, 200

    @admin_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('prj_name', type=str, required=True, help="Project Name is required")
        parser.add_argument('prj_start', type=str, required=True, help="Start Date required")
        parser.add_argument('prj_end', type=str, required=True, help="End Date is required")
        args = parser.parse_args()
        prj_name = args['prj_name']
        prj_start = args['prj_start']
        prj_end = args['prj_end']
        result=create_project(prj_name,prj_start,prj_end)

        if(result==LoginResult.NAME_EXIST):
            return {"msg":"Project Name Exist"},400
        if(result==LoginResult.INVALID_DATE):
            return {"msg":"Invalid Date"},400

        return {"msg":"success"},200
    
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('prj_name', type=str, required=True, help="Project Name is required")
        parser.add_argument('prj_start', type=str, required=True, help="Start Date required")
        parser.add_argument('prj_end', type=str, required=True, help="End Date is required")
        args = parser.parse_args()
        prj_name = args['prj_name']
        prj_start = args['prj_start']
        prj_end = args['prj_end']
    @admin_required()
    def delete(self,project_no):
        result=delete_project(project_no)
        if(result==DeleteResult.ALREADY_DELETE):
            return {"msg":"aleady delete"},400
        return {"msg":"success"},200