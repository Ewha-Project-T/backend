from flask import jsonify, Flask, request, make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.feedback_service import get_feedback_info, get_json_textae

class Feedback_textae(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int)
        parser.add_argument('user_no', type=int)
        args = parser.parse_args()
        as_no=args['as_no']
        user_no = args['user_no']
        url,review=get_json_textae(as_no,user_no)
        if review is -1:
            return jsonify({"msg": url, "isSuccess":False})
        if review is -2:
            return jsonify({"msg": url, "isSuccess":False})
        return jsonify({"url":url,"isSuccess":True})
    #TODO: api테스트 완료 후 jwt 적용
    # @jwt_required()
    # def post(self):
    #     parser = reqparse.RequestParser()
    #     parser.add_argument('lecture_no', type=int)
    #     parser.add_argument('as_no', type=int)
    #     parser.add_argument('user_no', type=int)
    #     parser.add_argument('ae_denotations', type=str,action='append')
    #     parser.add_argument('ae_attributes', type=str, action='append')
    #     parser.add_argument('result', type=str) # 총평
    #     parser.add_argument('DeliverIndividualList', type=int, action='append')
    #     parser.add_argument('ContentIndividualList', type=int, action='append')
    #     args = parser.parse_args()
    #     as_no=args['as_no']
    #     lecture_no = args['lecture_no']
    #     user_no = args['user_no']
    #     ae_denotations = str(args['ae_denotations']).replace('"',"")
    #     ae_attributes = str(args['ae_attributes']).replace('"',"")
    #     result=args['result']
    #     dlist=args['DeliverIndividualList']
    #     clist=args['ContentIndividualList']
    #     save_json_feedback(as_no,lecture_no,user_no,ae_attributes,ae_denotations,result,dlist,clist)
    #     return jsonify({"isSuccess":True})

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
