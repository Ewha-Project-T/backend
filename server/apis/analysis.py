from flask import jsonify, send_file
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.services.login_service import delete
from ..services.analysis_service import *
from ..services.xml_parser import add_vuln
import time
import pandas as pd

class Analysis(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('xml_no', type=str, required=True, help="File Not Found")
        args = parser.parse_args()
        xml_no = args['xml_no']
        xlsx_file = make_xlsx(xml_no)
        send = send_file(xlsx_file)
        os.remove(xlsx_file)
        return send
        
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files', action='append')
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
        safe = []
        vuln = []
        #safe, vuln = add_vuln(path)
        for i in range(len(path)):
            tmp_safe, tmp_vuln = add_vuln(path[i])
            safe.append(tmp_safe)
            vuln.append(tmp_vuln)
        
        insert_db(upload_time, path, safe, vuln)
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
        parser.add_argument('xml_no', type=str, required=True, help="FileName is required")
        args = parser.parse_args()

        xml_no = args['xml_no']
        result = delete_analysis_file(xml_no)
        if(result == DeleteResult.SUCCESS):
            return {"msg":"ok"}, 200
        else:
            return {"msg": "fail"}, 401

class Hosts(Resource):
    @jwt_required()
    def get(self,proj_no):
        current_user = get_jwt_identity()
        if(proj_no != str(current_user["project_no"])):
            return {"msg":"Forbidden Project"}, 403
        hosts = get_hosts(proj_no)
        return jsonify(hosts=hosts)

class HostAnalysis(Resource):
    @jwt_required()
    def get(self,proj_no,host_no):
        current_user = get_jwt_identity()
        if(proj_no != str(current_user["project_no"])):
            return {"msg":"Forbidden Project"}, 403
        analysises = get_host_analysis(host_no)
        return jsonify(analysises=analysises)

class ProjectAnalysis(Resource):
    @jwt_required()
    def get(self):
        '''
        current_project = get_jwt_identity()
        if(proj_no != str(current_project["project_no"])):
            return {"msg":"Access Denied"}, 403
            '''
        proj_analysises = get_project_analysis()
        return jsonify(proj_analysises=proj_analysises)