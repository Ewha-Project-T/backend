from flask import jsonify, send_file
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
from server.services.login_service import delete
from ..services.analysis_service import *
from ..services.xml_parser import add_vuln
import time



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
        parser.add_argument('project_no', type=int, required=True, help="Project_no is required")
        parser.add_argument('user_no', type=int, required=True, help="User_no is required")
        args = parser.parse_args()
        
        fd = args['file']
        
        filename = secure_filename(fd[0].filename)
        result ,file_ext = get_file_ext(filename)
        
        uploaded_path = upload_file(fd)
        
        # Insert 'uploaded_path' in DB 
        if(result == ExtensionsResult.SUCCESS):
            if file_ext == "zip" or file_ext == "tar":
                path = compression_extract(uploaded_path , file_ext)
            else:
                path = [uploaded_path]
        else:
            return{"msg":"denied file extensions"}, 400
        '''
        insert paring code ()
        save parinsg result
        '''
        upload_time = time.strftime("%Y-%m-%d %H:%M:%S")
        project_no = args['project_no']
        user_no = args['user_no']
        safe = []
        vuln = []
        #safe, vuln = add_vuln(path)
        for i in range(len(path)):
            tmp_safe, tmp_vuln = add_vuln(path[i])
            safe.append(tmp_safe)
            vuln.append(tmp_vuln)
        
        insert_db(upload_time, project_no, user_no, path, safe, vuln)
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