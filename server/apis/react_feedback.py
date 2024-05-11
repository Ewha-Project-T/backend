from curses.panel import update_panels
import json
from flask import jsonify, Flask, request, make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.feedback_service import get_all_graphs, get_feedback_info, get_feedback_review, get_json_textae, get_my_graphs, get_self_feedback_info, get_self_json_textae, get_zip_url, put_json_textae, save_feedback_review, update_graph, update_open

class Feedback_textae(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('as_no', type=int)
    parser.add_argument('user_no', type=int)
    @jwt_required()
    def get(self):
        args = self.parser.parse_args()
        as_no=args['as_no']
        user_no = args['user_no']
        textae, new_attribute, review=get_json_textae(as_no,user_no)
        if review is False:
            return jsonify({"message": textae,"isSuccess":False})
        return jsonify({"textae": textae, "new_attribute": new_attribute,"isSuccess":True})
    @jwt_required()
    def put(self):
        self.parser.add_argument('ae_denotations', type=str, action='append')
        self.parser.add_argument('ae_attributes', type=str, action='append')
        args = self.parser.parse_args()
        as_no=args['as_no']
        user_no = args['user_no']
        ae_denotations = str(args['ae_denotations']).replace('"',"")
        ae_attributes = str(args['ae_attributes']).replace('"',"")
        msg, status= put_json_textae(as_no,user_no,ae_denotations,ae_attributes)
        if status is False:
            return jsonify({"msg": msg, "isSuccess":False})
        return jsonify({"msg": msg, "isSuccess":True})
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

class Feedback_self_textae(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('as_no', type=int)
    parser.add_argument('user_no', type=int)
    @jwt_required()
    def get(self):
        args = self.parser.parse_args()
        as_no=args['as_no']
        user_no = args['user_no']
        textae, new_attribute, review=get_self_json_textae(as_no,user_no)
        if review is False:
            return jsonify({"message": textae,"isSuccess":False})
        return jsonify({"textae": textae, "new_attribute": new_attribute,"isSuccess":True})
    @jwt_required()
    def put(self):
        self.parser.add_argument('ae_denotations', type=str, action='append')
        self.parser.add_argument('ae_attributes', type=str, action='append')
        args = self.parser.parse_args()
        as_no=args['as_no']
        user_no = args['user_no']
        ae_denotations = str(args['ae_denotations']).replace('"',"")
        ae_attributes = str(args['ae_attributes']).replace('"',"")
        msg, status= put_json_textae(as_no,user_no,ae_denotations,ae_attributes)
        if status is False:
            return jsonify({"msg": msg, "isSuccess":False})
        return jsonify({"msg": msg, "isSuccess":True})

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

class Feedback_self_info(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int, required=True)
        args = parser.parse_args()
        as_no = args['as_no']
        user_info = get_jwt_identity()
        res = get_self_feedback_info(as_no, user_info['user_no'])
        return jsonify(res)

class Feedback_review(Resource):

    def _parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int, required=True)
        parser.add_argument('student_no', type=int, required=True)
        return parser.parse_args()

    def _get_user_info(self):
        return get_jwt_identity()

    @jwt_required()
    def get(self):
        args = self._parse_args()
        user_info = self._get_user_info()
        res = get_feedback_review(args['as_no'], args['student_no'], user_info['user_no'])
        return jsonify(res)

    @jwt_required()
    def post(self):
        args = self._parse_args()
        args.update({'review': self._parse_review()})
        user_info = self._get_user_info()
        res = save_feedback_review(args['as_no'], args['student_no'], user_info['user_no'], args['review'])
        return jsonify(res)

    def _parse_review(self):
        parser = reqparse.RequestParser()
        parser.add_argument('review', type=str, required=True)
        return parser.parse_args().get('review')

class Feedback_professor_graph(Resource):

    def _parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int, required=True)
        return parser.parse_args()
    
    @jwt_required()
    def get(self):
        args = self._parse_args()
        user_info = get_jwt_identity()
        res = get_all_graphs(args['as_no'], user_info['user_no'])
        return jsonify(res)

class Feedback_student_graph(Resource):
    def _parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int, required=True)
        return parser.parse_args()
        
    @jwt_required()
    def get(self):
        args = self._parse_args()
        user_info = get_jwt_identity()
        res = get_my_graphs(args['as_no'], user_info['user_no'])
        return jsonify(res)

class Feedback_graph_update(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int, required=True)
        parser.add_argument('student_no', type=int, required=True)
        args = parser.parse_args()
        user_info = get_jwt_identity()
        res = update_graph(as_no=args['as_no'], user_no=args['student_no'])
        return jsonify({"isSuccess":True})
    
class Feedback_open(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('as_no', type=int, required=True)
        parser.add_argument('open', type=bool, required=True)
        args = parser.parse_args()
        user_info = get_jwt_identity()
        res = update_open(as_no=args['as_no'], user_no=user_info['user_no'], open=args['open'])
        return jsonify({"isSuccess":True})

class assignment_zip_down(Resource): # 과제 압축파일 다운로드 개발 후 삭제
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lecture_no', type=int, required=True)
        parser.add_argument('user_no', type=int, required=True)
        args=parser.parse_args()
        path = get_zip_url(args['lecture_no'],args['user_no'])
        return jsonify({"url":path,
                        "file_name":path.split('/')[-1],
                        "isSuccess":True,
                        })
