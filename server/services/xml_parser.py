from xml.etree.ElementTree import parse, XMLParser
from flask_restful import reqparse
from flasgger import swag_from
from flask_jwt_extended import jwt_required
from server import db
from ..model import Code

class ParseResult:
    SUCCESS = 0
    INVALID_FILE = 1

def parse_xml(file_name):
    #file_name = "OS_Linux_LUCYSWORD_172.17.114.118.xml" # 샘플 xml
    path = "uploads/" # 경로는 추후에 파일 실제 저장 경로로 맞춰야함
    encoding = XMLParser(encoding="utf-8")
    try:
        tree = parse(path + file_name, parser=encoding)
    except:
        return ParseResult.INVALID_FILE, {'msg':'File Not Found'}, 400, None, None, None, None, None

    root = tree.getroot()

    row = root.findall("row")
    #total_cnt = len(row) # 항목 
    group_code = [x.findtext("Group_Code") for x in row]
    group_name = [x.findtext("Group_Name") for x in row]
    title_code = [x.findtext("Title_Code") for x in row]
    title_name = [x.findtext("Title_Name") for x in row]
    important = [x.findtext("Import") for x in row]
    decision = [x.findtext("Decision") for x in row]
    issue = [x.findtext("Issue") for x in row]

    codes = []
    for title in title_code:
        acc = Code.query.filter_by(title_code=title).first()
        if(acc == None):
            codes.append(None)
        else:
            codes.append(acc.kisa_code)
    
    return ParseResult.SUCCESS, group_code, group_name, title_code, title_name, important, decision, issue, codes

def add_vuln(file_name):
    path = "uploads/" # 경로는 추후에 파일 실제 저장 경로로 맞춰야함
    encoding = XMLParser(encoding="utf-8")
    safe = []
    vuln = []
    try:
        tree = parse(path + file_name, parser=encoding)
    except:
        return ParseResult.INVALID_FILE, {'msg':'File Not Found'}, 400, None, None, None, None, None

    root = tree.getroot()
    row = root.findall("row")
    decision = [x.findtext("Decision") for x in row]
    safe = decision.count('양호')
    vuln = decision.count('취약')
    return safe, vuln