from xml.etree.ElementTree import parse, XMLParser
from flask_restful import reqparse
from flasgger import swag_from
from flask_jwt_extended import jwt_required
from server import db
from ..model import Code, Analysis, HostInfo

class ParseResult:
    SUCCESS = 0
    INVALID_FILE = 1

def parse_xml(xml_no):
    path = "uploads/"
    encoding = XMLParser(encoding="utf-8")
    xml_row = Analysis.query.filter_by(xml_no=xml_no).first()
    file_name = xml_row.path
    try:
        tree = parse(path + file_name, parser=encoding)
    except:
        return ParseResult.INVALID_FILE

    root = tree.getroot()

    row = root.findall("row")
    group_code = [x.findtext("Group_Code") for x in row]
    group_name = [x.findtext("Group_Name") for x in row]
    title_code = [x.findtext("Title_Code") for x in row]
    title_name = [x.findtext("Title_Name") for x in row]
    important = [x.findtext("Import") for x in row]
    decision = [x.findtext("Decision") for x in row]
    issue = [x.findtext("Issue") for x in row]

    codes = []
    for title in title_code:
        kcode = Code.query.filter_by(title_code=title).first()
        if(kcode == None):
            codes.append(None)
        else:
            codes.append(kcode.kisa_code)
            
    parsed = {}
    parsed["group_code"] = group_code
    parsed["group_name"] = group_name
    parsed["title_code"] = title_code
    parsed["title_name"] = title_name
    parsed["important"] = important
    parsed["decision"] = decision
    parsed["issue"] = issue
    parsed["codes"] = codes
    
    return parsed

def add_vuln(file_name):
    path = "uploads/"
    encoding = XMLParser(encoding="utf-8")
    safe = []
    vuln = []
    try:
        tree = parse(path + file_name, parser=encoding)
    except:
        return ParseResult.INVALID_FILE, 0, 0

    root = tree.getroot()
    row = root.findall("row")
    decision = [x.findtext("Decision") for x in row]
    safe = decision.count('양호')
    vuln = decision.count('취약')
    return ParseResult.SUCCESS, safe, vuln
