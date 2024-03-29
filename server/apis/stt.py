import base64
import uuid
import os

from flask import jsonify, Response, abort
from flask_restful import reqparse, Resource
from flask_restful.reqparse import Argument
from flask_jwt_extended import jwt_required,get_jwt_identity
from sqlalchemy.ext.declarative import DeclarativeMeta

import werkzeug
import json

from ..services.stt_service import simultaneous_stt, get_userfile, is_stt_userfile, mapping_sst_user, remove_userfile, stt_getJobResult
import azure.cognitiveservices.speech as speechsdk

class APIArgument(Argument):
    def __init__(self, *args, **kwargs):
        super(APIArgument, self).__init__(*args, **kwargs)

    def handle_validation_error(self, error, bundle_errors):
        help_str = "(%s) " % self.help if self.help else ""
        msg = "[%s]: %s%s" % (self.name, help_str, str(error))
        res = Response(
            json.dumps({"message": msg, "code": 400, "status": "FAIL"}),
            mimetype="application/json",
            status=400,
        )
        return abort(res)

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

class Stt(Resource):
    @jwt_required()
    def get(self):
        user_info=get_jwt_identity()
        files = get_userfile(user_info)
        if not files:
            return { "msg": "user stt is not exists" },404
        return jsonify(files=AlchemyEncoder().default(files))
    
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser(argument_class=APIArgument, bundle_errors=True)
        parser.add_argument('assignment', type=int, required=True, help="assignment is required")
        parser.add_argument('file', type=uuid.UUID, required=True, help="file is required")
        parser.add_argument("locale", type=str, default="ko-KR", help="locale is required(default=ko-KR)")

        args = parser.parse_args()
        assignment = args['assignment']
        file = args['file']
        locale = args['locale']
        
        user_info=get_jwt_identity()
        if not is_stt_userfile(assignment, file,user_info):
            return { "msg": "user stt is not exists" },404

        jobid = simultaneous_stt(file, locale)

        return jsonify(job=jobid)

    @jwt_required()
    def put(self):
        file = str(uuid.uuid4())
        filename = f"{file}.mp3"
        parser = reqparse.RequestParser(argument_class=APIArgument, bundle_errors=True)
        parser.add_argument('assignment', type=int, required=True, help="assignment is required")
        parser.add_argument("mp3", type=werkzeug.datastructures.FileStorage, location="files", required=True, help="mp3 is required")
        
        args = parser.parse_args()
        assignment = args['assignment']
        mp3 = args['mp3']
        
        mp3.save(f"{os.environ['UPLOAD_PATH']}/{filename}")
        user_info=get_jwt_identity()
        mapping_sst_user(assignment, file,user_info)
        return jsonify(file=file)

    @jwt_required()
    def delete(self):
        parser = reqparse.RequestParser(argument_class=APIArgument, bundle_errors=True)
        parser.add_argument('assignment', type=int, required=True, help="assignment is required")
        parser.add_argument('file', type=uuid.UUID, required=True, help="file is required")
        
        args = parser.parse_args()
        assignment = args['assignment']
        file = args['file']
        user_info=get_jwt_identity()
        if remove_userfile(assignment, file,user_info):
            return jsonify(msg="success")
        else:
            return { "msg": "user stt is not exists" },404

class SttJob(Resource):
    def get(self, jobid):
        return jsonify(stt_getJobResult(jobid))

class SttSeq(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser(argument_class=APIArgument, bundle_errors=True)
        parser.add_argument('assignment', type=int, required=True, help="assignment is required")
        parser.add_argument('region', type=dict, action='append', required=True, help="region is required")
        parser.add_argument('file', type=uuid.UUID, required=True, help="file is required")

        args = parser.parse_args()
        
        assignment = args['assignment']
        region = args['region']
        file = args['file']

        param = []
        try:
            for item in region:
                param += [ (int(item["start"]), int(item["end"])) ]
        except:
            return jsonify({"msg": "start, end is required"})

        if not is_stt_userfile(assignment, file):
            return { "msg": "user stt is not exists" },404

        jobid = sequential_stt(file, param)
        return jsonify(job=jobid)

class SttSeqJob(Resource):
    def get(self, jobid):
        return jsonify(seqstt_getJobResult(jobid))