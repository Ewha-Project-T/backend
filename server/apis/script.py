from flask import jsonify, send_file, send_from_directory
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
import werkzeug
import os

BASE_PATH = "script_files/"

def existFile(path):
    res = os.path.isfile(path)
    return res

class ScriptAPI(Resource):
    @jwt_required()
    def get(self,fname):
        file_path = BASE_PATH + fname
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
        if(existFile(BASE_PATH + file_object.filename)):
            return {"msg": "Filename is duplicated."}, 400
        else:
            file_object.save(BASE_PATH + file_object.filename)
            return {"msg":"success"}, 200

