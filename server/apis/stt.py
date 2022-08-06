import base64
import uuid
import os

from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required

from app.server.services.stt_service import get_userfile, is_stt_userfile, mapping_sst_user, remove_userfile
from stt.stt import simultaneous_stt
 
class Stt(Resource):
    @jwt_required
    def get(self):
        files = get_userfile()
        if not files:
            return { "msg": "user stt is not exists" },404
        return jsonify(files=files)
    
    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('homework', type=int, required=True, help="homework is required")
        parser.add_argument('file', type=uuid.UUID, required=True, help="file is required")
        args = parser.parse_args()
        homework = args['homework']
        file = args['file']

        if not is_stt_userfile(homework, file):
            return { "msg": "user stt is not exists" },404

        return jsonify(
            simultaneous_stt(f"{os.getenv['UPLOAD_PATH']}/{file}.wav")
        )

    @jwt_required
    def put(self):
        file = str(uuid.uuid4())
        filename = f"{file}.wav"
        parser = reqparse.RequestParser()
        parser.add_argument('homework', type=int, required=True, help="homework is required")
        parser.add_argument("wav", type=str, required=True, help="wav is required")
        args = parser.parse_args()
        homework = args['homework']
        wav = args['wav']
        wavbin = None
        try:
            wavbin = base64.b64decode(wav)
        except:
            return { "msg": "Invalid wav file" },400

        with open(f"{os.getenv('UPLOAD_PATH')}/{filename}", "wb") as f:
            f.write(wavbin)

        mapping_sst_user(homework, file)
        return jsonify(file=file)

    @jwt_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('homework', type=int, required=True, help="homework is required")
        parser.add_argument('file', type=uuid.UUID, required=True, help="file is required")
        args = parser.parse_args()
        homework = args['homework']
        file = args['file']

        if remove_userfile(homework, file):
            return jsonify(msg="success")
        else:
            return { "msg": "user stt is not exists" },404