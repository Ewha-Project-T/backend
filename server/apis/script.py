from flask import jsonify, send_file
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ..services.admin_service import all_script_listing, all_project_script_listing
from ..services.login_service import admin_required, pm_required
from ..services.script_service import (
    upload_script, upload_formatter, UploadResult, script_listing, 
    DownloadAuthResult, download_auth_check, delete_script, DeleteResult
)
import werkzeug
import os

BASE_PATH = "script_files/"
ALLOW_EXTENSION = ["txt","bat","exe","sh"]
TYPE = ["Web","Server","Device"]

def existFile(path):
    res = os.path.isfile(path)
    return res

class ScriptAPI(Resource):
    @jwt_required()
    def get(self,fname):
        current_user = get_jwt_identity()
        file_path = BASE_PATH + secure_filename(fname)
        if(existFile(file_path)):
            if(download_auth_check(current_user["project_no"], fname) == DownloadAuthResult.SUCCESS):
                return send_file(file_path, as_attachment=True, attachment_filename='')
            else:
                return {"msg": "check your project"}, 400
        else:
            return {'msg':'File is not exist'}, 404
            
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=werkzeug.datastructures.FileStorage, location='files', required=True, help="Not Valid File")
        args = parser.parse_args()
        file_object = args['file_name']
        filename = secure_filename(file_object.filename)
        filename = upload_formatter(filename)
        if(existFile(BASE_PATH + filename)):
            return {"msg": "Filename is duplicated."}, 400
        elif(filename.split(".")[-1] not in ALLOW_EXTENSION):
            return {"msg": "Not Allowed extension"}, 403
        else:
            db_upload_result = upload_script("web",get_jwt_identity()["project_no"],filename)
            if(db_upload_result == UploadResult.SUCCESS):    
                file_object.save(BASE_PATH + secure_filename(filename))
                return {"msg":"success"}, 200
            elif(db_upload_result == UploadResult.DUPLICATED_NAME):
                return {"msg":"Filename is duplicated in DB"}, 400
                
    @admin_required()
    def delete(self,fname):
        file_path = BASE_PATH + secure_filename(fname)
        if(existFile(file_path)):
            if(delete_script(secure_filename(fname), file_path)==DeleteResult.SUCCESS):
                return {"msg": "delete success"}, 200
            else:
                return {"msg": "delete faile"}, 400
        else:
            return {'msg':'File is not exist'}, 404

class ScriptListingAPI(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        script_list = script_listing(current_user["project_no"])
        return jsonify(script_list=script_list)
    
class AdminScript(Resource):
    @pm_required()
    def get(self):
        current_user = get_jwt_identity()
        if(current_user["user_perm"] == 2):
            script_list = all_script_listing()
        else:
            script_list = all_project_script_listing(current_user["project_no"])
        return jsonify(all_script_list=script_list)

    @admin_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=str, required=True, help="Need Script Type")
        parser.add_argument('proj_no', type=str, required=True, help="Need Project Number")
        parser.add_argument('file_name', type=werkzeug.datastructures.FileStorage, location='files', required=True, help="Not Valid File")
        args = parser.parse_args()
        type = args['type']
        project_no = args['proj_no']
        file_object = args['file_name']
        if(type not in TYPE):
            return {"msg": "Invalid Script Type"}, 400
        filename = secure_filename(file_object.filename)
        filename = upload_formatter(filename)
        if(existFile(BASE_PATH + filename)):
            return {"msg": "Filename is duplicated."}, 400
        elif(filename.split(".")[-1] not in ALLOW_EXTENSION):
            return {"msg": "Not Allowed extension"}, 403
        else:
            db_upload_result = upload_script(type,project_no,filename)
            if(db_upload_result == UploadResult.SUCCESS):    
                file_object.save(BASE_PATH + secure_filename(filename))
                return {"msg":"success"}, 200
            elif(db_upload_result == UploadResult.INVALID_PROJECT_NO):
                return {"msg": "Invalid Project No"}, 400
            elif(db_upload_result == UploadResult.DUPLICATED_NAME):
                return {"msg":"Filename is duplicated in DB"}, 400

