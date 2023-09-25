from flask import jsonify, Flask, request, make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.feedback_service import get_feedback_info

class Feedback_info(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('as_no', type=int, required=True)
    parser.add_argument('student_no', type=int, required=True)
    @jwt_required()
    def get(self):
        args = self.parser.parse_args()
        as_no = args['as_no']
        student_no = args['student_no']
        user_info = get_jwt_identity()
        res = get_feedback_info(as_no, student_no, user_info['user_no'])
        return jsonify(res)
