from flask import jsonify, send_file, send_from_directory
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from ..services.script_service import upload_script, upload_formatter, UploadResult
import werkzeug
import os

BASE_PATH = "script_files/"
ALLOW_EXTENSION = ["txt","bat","exe"]

def existFile(path):
    res = os.path.isfile(path)
    return res

class ScriptAPI(Resource):
    @jwt_required()
    def get(self,fname):
        file_path = BASE_PATH + secure_filename(fname)
        if(existFile(file_path)):
            return send_file(file_path, as_attachment=True, attachment_filename='')
        else:
            return {'msg':'File is not exist'}, 400
            
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
            db_upload_result = upload_script("web",1,filename)
            if(db_upload_result == UploadResult.SUCCESS):    
                file_object.save(BASE_PATH + secure_filename(file_object.filename))
                return {"msg":"success"}, 200
            elif(db_upload_result == UploadResult.DUPLICATED_NAME):
                return {"msg":"Filename is duplicated in DB"}, 402

