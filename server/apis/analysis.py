from flask import jsonify
from werkzeug.datastructures import FileStorage
from werkzeug import secure_filename
from flask_restful import reqparse, Resource
from ..services.login_service import login_required
from ..services.scan_service import *

UPLOAD_PATH ='./'
class Analysis(Resource):
    @login_required()
    def get(self):
        return {"msg":"scanAPI"}, 200

    @login_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files', action='append')
        args = parser.parse_args()

        f = args['file']
        filename = secure_filename(f.filename)
        file_ext = get_file_ext(filename)

        f.save(UPLOAD_PATH + filename) #file save

        if file_ext == "zip" or file_ext == "tar":
            compression_extract(UPLOAD_PATH+filename , file_ext, "./")
            
        return {"msg":"ok"}, 200



    @login_required()
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="FileName is required")
        args = parser.parse_args()
        filename = args['file_name']
        return {"msg":filename}, 200
        