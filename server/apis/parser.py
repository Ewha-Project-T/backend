from flask_restful import reqparse, Resource
from flasgger import swag_from
from flask_jwt_extended import (
		jwt_required, get_jwt_identity, get_jwt
)
import re
from ..services.xml_parser import parse_xml, ParseResult
from ..services.analysis_service import add_vuln

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
            xml_result = []
            safe = decision.count('양호')
            vuln = decision.count('취약')
            add_vuln(xml_name, safe, vuln)
            for i in range(len(group_code)):
                #xml_result.append(["{ group_code : \"" + group_code[i] + "\",title_code : \"" + title_code[i] + "\",title_name : \"" + title_name[i] + "\",important : \"" + important[i] + "\",decision : \"" + decision[i] + "\",issue : \"" + issue[i] + "\" }"])
                xml_result.append({ 'group_code' : group_code[i],'group_name' : group_name[i],'title_code' : title_code[i],'title_name' : title_name[i],'important' : important[i],'decision' : decision[i],'issue' : issue[i]})
            return xml_result
            #return {"msg":"success"}, 200
        else:
            return {"msg":"invalid file name"}, 401
			
