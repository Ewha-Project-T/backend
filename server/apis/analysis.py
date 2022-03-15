from flask import jsonify
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask_restful import reqparse, Resource
from ..services.login_service import login_required
from ..services.analysis_service import *

UPLOAD_PATH ='../../uploads'
class Analysis(Resource):
    @login_required()
    def get(self):

        


        return {"msg":"scanAPI"}, 200

    @login_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files', action='append')
        args = parser.parse_args()

        fd = args['file']
        filename = secure_filename(fd.filename)
        file_ext = get_file_ext(filename)

        
        uploaded_path = upload_file(fd)
        
        #insert sql uploaded_path

        if file_ext == "zip" or file_ext == "tar":
            compression_extract(uploaded_path , file_ext)



        '''
        insert paring code ()
        save parinsg result

        '''
            
        return {"msg":"ok"}, 200



    @login_required()
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="FileName is required")
        args = parser.parse_args()
        filename = args['file_name']
        
        return {"msg":filename}, 200
        