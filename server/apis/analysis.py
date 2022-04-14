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
        result, xlsx_file = make_xlsx(xml_no)
        if(result == XlsxResult.NO_ARGS):
            return {"msg" : "No Argments"}, 404
        elif(result == XlsxResult.INVALID_FILE):
            return {"msg" : "No Search File"}, 404
        try:
            send = send_file(xlsx_file)
        except:
            return {"msg" : "File Download Fail"}, 403
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
            elif file_ext == "xml":
                path = [uploaded_path]
            else:
                return {"msg":"denied file extensions"}, 403
        elif (result == ExtensionsResult.DENIED_EXTENSIONS):
            return{"msg":"denied file extensions"}, 403
        else:
            return{"msg":"Invalid File Name"}, 403

        upload_time = time.strftime("%Y-%m-%d %H:%M:%S")
        safe = []
        vuln = []
        host_name = []
        ip = []
        types = []
        for i in range(len(path)):
            result, tmp_safe, tmp_vuln, tmp_host, tmp_ip, tmp_os = add_vuln(path[i])
            if(result == ParseResult.INVALID_FILE):
                return {"msg" : "Invalid File"}, 404
            safe.append(tmp_safe)
            vuln.append(tmp_vuln)
            host_name.append(tmp_host)
            ip.append(tmp_ip)
            types.append(tmp_os)
        
        insert_db(upload_time, path, safe, vuln, host_name, ip, types)
        return {"msg":"ok"}, 200

    @jwt_required()
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="FileName is required")
        args = parser.parse_args()
        filename = args['file_name']
        
        return {"msg":filename}, 200
    
    @jwt_required()
    def patch(self):
        parser = reqparse.RequestParser()
        parser.add_argument('host_no', type=int, required=True, help="host no is required")
        parser.add_argument('host_name', type=str)
        parser.add_argument('ip', type=str)
        parser.add_argument('types', type=str)
        args = parser.parse_args()
        host_no = args['host_no']
        host_name = args['host_name']
        ip = args['ip']
        types = args['types']
        res = modify_host(host_no, host_name, ip, types)
        if(res == HostInfoResult.INVALID_HOST):
            return {"msg":"Invalid host"}, 404
        elif(res == HostInfoResult.INVALID_PROJECT):
            return {"msg":"Invalid project"}, 403
        elif(res == HostInfoResult.DUPLICATED_NAME):
            return {"msg":"Duplicated name"}, 400
        return {"msg":host_name}, 200

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
            return {"msg": "Analysis Delete Fail"}, 403

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
        proj_analysises = get_project_analysis()
        return jsonify(proj_analysises=proj_analysises)
        
class Comments(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('xml_no', type=int, required=True, help="xml_no is required")
        parser.add_argument('title_code', type=str, required=True, help="title_code is required")
        args = parser.parse_args()
        xml_no = args['xml_no']
        title_code = args['title_code']

        result, comment = get_comments(xml_no, title_code)
        if(result == CommentingResult.INVALID_PROJECT_NO):
            return {"msg":"Invalid Project No"}, 404
        elif(result == CommentingResult.NOCOMMENT):
            return ''
        else:
            return jsonify(comment=comment)

    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('xml_no', type=int, required=True, help="xml_no is required")
        parser.add_argument('title_code', type=str, required=True, help="title_code is required")
        parser.add_argument('comment', type=str, required=True, help="comments is required")
        parser.add_argument('vuln', type=str, required=True, help="vuln is required")
        args = parser.parse_args()

        xml_no = args['xml_no']
        title_code = args['title_code']
        comments = args['comment']
        vuln = args['vuln']
        
        result = commenting(xml_no, title_code, comments, vuln)
        if(result == CommentingResult.SUCCESS):
            return {"msg":"success"}, 200
        elif(result == CommentingResult.INVALID_PROJECT_NO):
            return {"msg":"Invalid Project"}, 404
        elif(result == ComementingResult.INVALID_FILE):
            return {"msg":"Invalid File"}, 404
        elif(result == CommentingResult.WRITE_FAIL):
            return {"msg":"XML Patch Fail"}, 404
        elif(result == CommentingResult.INVALID_DECISION):
            return {"msg":"Invaild Decision"}, 404
        else:
            return {"msg":"Internal Error"}, 400
    
    @jwt_required()
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('comment_no', type=str, required=True, help="comments is required")
        args = parser.parse_args()

        comment_no = args['comment_no']

        result = delete_comment(comment_no)
        
        if(result == CommentingResult.SUCCESS):
            return {"msg":"success"}, 200
        elif(result == CommentingResult.INVALID_PROJECT_NO):
            return {"msg":"Invalid xml"}, 404
        elif(result == CommentingResult.INVALID_FILE):
            return {"msg":"Invalid File"}, 404
        elif(result == CommentingResult.WRITE_FAIL):
            return {"msg":"XML Patch Fail"}, 404
        elif(result == CommentingResult.INVALID_COMMENT):
            return {"msg":"Invaild Comment"}, 404
        elif(result == CommentingResult.INVALID_XML):
            return {"msg":"Invaild XML No"}, 404
        else:
            return {"msg":"Internal Error"}, 400

    @jwt_required()
    def patch(self):
        parser = reqparse.RequestParser()
        parser.add_argument('comment', type=str, required=True, help="comments is required")
        parser.add_argument('comment_no', type=str, required=True, help="comments is required")
        args = parser.parse_args()
        
        comment = args['comment']
        comment_no = args['comment_no']

        result = patch_comment(comment, comment_no)

        if(result == CommentingResult.SUCCESS):
            return {"msg":comment}, 200
        elif(result == CommentingResult.INVALID_PROJECT_NO):
            return {"msg":"Invalid project_no"}, 404
        elif(result == CommentingResult.INVALID_COMMENT):
            return {"msg":"Invaild Comment"}, 404
        elif(result == CommentingResult.INVALID_XML):
            return {"msg":"Invaild XML No"}, 404
        else:
            return {"msg":"Internal Error"}, 400
