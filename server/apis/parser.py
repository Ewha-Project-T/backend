from flask_restful import reqparse, Resource
from flasgger import swag_from
from ..services.xml_parser import parse_xml


class XML_Parser(Resource):
    @swag_from("../../docs/parser/post.yml")
    #@jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('xml_no', type=str, required=True, help="File Not Found")
        args = parser.parse_args()
        xml_no = args['xml_no']
        parsed = parse_xml(xml_no)
        if(type(parsed)==type({})):
            xml_result = []
            for i in range(len(parsed["group_code"])):
                xml_result.append({ 'group_code' : parsed["group_code"][i],
                    'group_name' : parsed["group_name"][i],
                    'title_code' : parsed["title_code"][i],
                    'title_name' : parsed["title_name"][i],
                    'important' : parsed["important"][i],
                    'decision' : parsed["decision"][i],
                    'issue' : parsed["issue"][i], 
                    'code' : parsed["codes"][i]})
            safe = parsed["decision"].count('양호')
            vuln = parsed["decision"].count('취약')
            xml_result = {'safe' : + safe , 'vuln' : vuln, 'details' : xml_result} 
            return xml_result
        else:
            return {"msg":"invalid file name"}, 404
			
