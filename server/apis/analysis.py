from flask import jsonify, send_file
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
from server.services.login_service import delete
from ..services.analysis_service import *


class Analysis(Resource):
    @jwt_required()
    def get(self,filename):

        file_path = ''# Get File Path From DB
        pure_name = os.path.basename(file_path)

        return send_file(file_path, as_attachment=True, attachment_filename=pure_name)


    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files', action='append')
        args = parser.parse_args()

        fd = args['file']
        filename = secure_filename(fd.filename)
        file_ext = get_file_ext(filename)

        
        uploaded_path = upload_file(fd)
        
        # Insert 'uploaded_path' in DB 

        if file_ext == "zip" or file_ext == "tar":
            compression_extract(uploaded_path , file_ext)

        '''
        insert paring code ()
        save parinsg result
        '''
            
        return {"msg":"ok"}, 200


    @jwt_required()
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="FileName is required")
        args = parser.parse_args()
        filename = args['file_name']
        
        return {"msg":filename}, 200
    
    @jwt_required()
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="FileName is required")
        args = parser.parse_args()

        filename = args['file_name']        

        file_path = ''# Get analysis file path From DB

        delete_analysis_file(file_path)

        return ''