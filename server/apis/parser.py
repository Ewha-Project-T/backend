from flask_restful import reqparse, Resource
from flasgger import swag_from
from flask_jwt_extended import (
		jwt_required, get_jwt_identity, get_jwt
)
import re
from ..services.xml_parser import parse_xml, ParseResult

class XML_Parser(Resource):
    @swag_from("../../docs/parser/post.yml")
    #@jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('xml_name', type=str, required=True, help="File Not Found")
        args = parser.parse_args()
        xml_name = args['xml_name']
        result, group_code, group_name, title_code, title_name, important, decision, issue = parse_xml(xml_name)
        if(result==ParseResult.SUCCESS):
            #return group_code, group_name, title_code, title_name, important, decision, issue
            return {"msg":"success"}, 200
        else:
            return {"msg":"invalid file name"}, 401
			
