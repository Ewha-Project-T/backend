from flask_restful import reqparse, Resource
from flasgger import swag_from
from flask_jwt_extended import (
		jwt_required, get_jwt_identity, get_jwt
)
import re
from ..services.xml_parser import xml_result, ParseResult

class Result(Resource):
    @swag_from("../../docs/result/parser.yml")
    #@jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file_name', type=str, required=True, help="File Not Found")
        args = parser.parse_args()
        file_name = args['file_name']
        result, group_code, group_name, title_code, title_name, important, decision, issue = xml_result(file_name)
        if(result==ParseResult.SUCCESS):
            #return group_code, group_name, title_code, title_name, important, decision, issue
            return {"msg":"success"}, 200
        else:
            return {"msg":"invalid file name"}, 401
			
