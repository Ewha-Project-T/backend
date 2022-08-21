import base64
import uuid
import os

from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required
import werkzeug

from ..services.stt_service import simultaneous_stt, get_userfile, is_stt_userfile, mapping_sst_user, remove_userfile, stt_getJobResult
import azure.cognitiveservices.speech as speechsdk

class Stt(Resource):
    @jwt_required
    def get(self):
        files = get_userfile()
        if not files:
            return { "msg": "user stt is not exists" },404
        return jsonify(files=files)
    
    # @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        # parser.add_argument('assignment', type=int, required=True, help="assignment is required")
        parser.add_argument('file', type=uuid.UUID, required=True, help="file is required")

        args = parser.parse_args()
        # assignment = args['assignment']
        file = args['file']

        # if not is_stt_userfile(assignment, file):
        #     return { "msg": "user stt is not exists" },404

        jobid = simultaneous_stt(file)

        return jsonify(job=jobid)

    # @jwt_required
    def put(self):
        file = str(uuid.uuid4())
        filename = f"{file}.wav"
        parser = reqparse.RequestParser()
        # parser.add_argument('assignment', type=int, required=True, help="assignment is required")
        parser.add_argument("wav", type=werkzeug.datastructures.FileStorage, location="files", required=True, help="wav is required")
        
        args = parser.parse_args()
        # assignment = args['assignment']
        wav = args['wav']
        
        wav.save(f"{os.environ['UPLOAD_PATH']}/{filename}")
        # mapping_sst_user(assignment, file)
        return jsonify(file=file)

    @jwt_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('assignment', type=int, required=True, help="assignment is required")
        parser.add_argument('file', type=uuid.UUID, required=True, help="file is required")
        
        args = parser.parse_args()
        assignment = args['assignment']
        file = args['file']

        if remove_userfile(assignment, file):
            return jsonify(msg="success")
        else:
            return { "msg": "user stt is not exists" },404

class SttJob(Resource):
    def get(self, jobid):
        return jsonify(stt_getJobResult(jobid))
