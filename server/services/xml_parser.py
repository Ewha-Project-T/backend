from xml.etree.ElementTree import parse, XMLParser
from flask_restful import reqparse
from flasgger import swag_from
from flask_jwt_extended import jwt_required
from server import db
from ..model import Code, Analysis, HostInfo
import os

class ParseResult:
    SUCCESS = 0
    INVALID_FILE = 1
    WRONG_XML = 2

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
    
    replace_entity(file_name)
    try:
        tree = parse(path + file_name, parser=encoding)
    except:
        return ParseResult.INVALID_FILE, 0, 0, 0, 0, 0
    root = tree.getroot()

    host_name = root.find("Hostname").text
    ip = root.find("Ipaddress").text
    types = root.find("OSversion").text
    row = root.findall("row")
    decision = [x.findtext("Decision") for x in row]
    safe = decision.count('양호')
    vuln = decision.count('취약')
    return ParseResult.SUCCESS, safe, vuln, host_name, ip, types

def replace_entity(file_name):
    path = 'uploads/'
    ALLOWED_ELEMENT = ['xml', 'rows', 'Hostname', 'Ipaddress', 'OSversion', 'OScode', 'row', 'Group_Code', 'Group_Name', 'Title_Code', 'Title_Code', 'Title_Name', 'Import', 'Decision', 'Issue']

    f = open(path + file_name, 'r')
    w = open(path + "tmp.xml", 'w')
    while True:
        line = f.readline()
        if not line: break
        if('<' in line):
            line = line.replace('<', '&lt;')
        if('>' in line):
            line = line.replace('>', '&gt;')
        w.write(line)
    
    f = open(path + "tmp.xml", 'r')
    w = open(path + file_name, 'w')
    while True:
        line = f.readline()
        if not line: break
        for i in range(len(ALLOWED_ELEMENT)):
            if(ALLOWED_ELEMENT[i] in line):
                line = line.replace('&lt;', '<')
                line = line.replace('&gt;', '>')
        w.write(line)

    f.close()
    w.close()
    os.remove(path + "tmp.xml")