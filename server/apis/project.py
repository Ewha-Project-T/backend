from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.login_service import admin_required, pm_required
from ..services.project_service import (
    create_project, delete_project,change_project,CreateResult,DeleteResult,ChangeResult,
    listing_project, enroll_project_scripts, EnrollResult
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

        if(result==CreateResult.NAME_EXIST):
            return {"msg":"Project Name Exist"}, 400
        if(result==CreateResult.INVALID_DATE):
            return {"msg":"Invalid Date"}, 400

        return {"msg":"success"}, 200
    @admin_required()
    def patch(self,project_no):
        parser = reqparse.RequestParser()
        parser.add_argument('prj_name', type=str)
        parser.add_argument('prj_start', type=str)
        parser.add_argument('prj_end', type=str)
        args = parser.parse_args()
        prj_name = args['prj_name']
        prj_start = args['prj_start']
        prj_end = args['prj_end']
        result=change_project(project_no, prj_name, prj_start, prj_end)
        if(result==ChangeResult.NAME_EXIST):
            return {"msg":"Project Name Exist"}, 400
        elif(result==ChangeResult.INVALID_DATE):
            return {"msg":"Invalid Date"}, 400
        
        return {"msg":"success"},200
    @admin_required()
    def delete(self,project_no):
        result=delete_project(project_no)
        if(result==DeleteResult.ALREADY_DELETE):
            return {"msg":"aleady delete"},400
        return {"msg":"success"},200

class ProjectList(Resource):
    @admin_required()
    def get(self):
        return jsonify(projects_info = listing_project())

class ProjectScripts(Resource):
    @pm_required()
    def post(self):
        current_user = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('script_no', type=int)
        args = parser.parse_args()
        script_no = args['script_no']
        result = enroll_project_scripts(current_user["project_no"], script_no)
        if(result == EnrollResult.INVALID_SCRIPT_NO):
            return {"msg":"Invalid Script"}, 404
        elif(result == EnrollResult.DUPLICATED_SCRIPT):
            return {"msg":"Duplicated Script"}, 403
        return {"msg":"success"}, 200
        
        