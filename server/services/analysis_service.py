import zipfile
import tarfile
import os
import time
import shutil
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
from werkzeug.utils import secure_filename
from server import db
from ..model import User, Analysis, HostInfo, Comment
from ..services.xml_parser import parse_xml, ParseResult
import pandas as pd
import xlsxwriter
from flask import send_file
from xml.etree.ElementTree import parse, XMLParser, dump

ALLOWED_EXTENSIONS = set(['zip', 'xml','tar'])
ALLOWED_DECISION = set(['양호', '취약', '수동점검', 'N/A'])
UPLOAD_PATH ='./uploads/'

class UploadResult:
    SUCCESS = 0
    INVALID_PROJECT_NO = 1
    INVALID_USER_NO = 2
    INVALID_PATH = 3
    UPLOAD_FAIL = 4

class DeleteResult:
    SUCCESS = 0
    INVALID_PROJECT_NO = 1
    INVALID_USER_NO = 2
    INVALID_PATH = 3
    DELETE_FAIL = 4

class DownloadResult:
    SUCCESS = 0
    INVALID_PROJECT_NO = 1
    INVALID_USER_NO = 2
    INVALID_PATH = 3
    Download_FAIL = 4

class ExtensionsResult:
    SUCCESS = 0
    DENIED_EXTENSIONS = 1

class VulnResult:
    SUCCESS = 0
    INVALID_PATH = 1

class CommentingResult:
    SUCCESS = 0
    INVALID_COMMENT = 1
    INVALID_PROJECT_NO = 2
    INVALID_FILE = 3
    WRITE_FAIL = 4
    INVALID_DECISION = 5
    INVALID_XML = 6
    NOCOMMENT = 7

class XlsxResult:
    SUCCESS = 0
    NO_ARGS = 1
    INVALID_FILE = 2

class HostInfoResult:
    SUCCESS = 0
    INVALID_HOST = 1
    DUPLICATED_NAME = 2

def compression_extract(file_path, ext):
    if ext == "zip":
        f = zipfile.ZipFile(UPLOAD_PATH + file_path)
    elif ext == "tar":
        f = tarfile.open(UPLOAD_PATH + file_path)

    f.extractall(UPLOAD_PATH + file_path.split('/')[0] + "/")
    os.remove(UPLOAD_PATH + file_path)
    f.close()
    path = []
    file_list = os.listdir(UPLOAD_PATH + file_path.split('/')[0] + "/")
    for i in range(len(file_list)):
        path.append(file_path.split('/')[0] + "/" + file_list[i])
    return path

def get_file_ext(filename):
    if '.' in filename:
        if filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS:
            return ExtensionsResult.SUCCESS, filename.rsplit('.',1)[1]
        else:
            return ExtensionsResult.DENIED_EXTENSIONS, ''
    return ''

def delete_analysis_file(xml_no):
    acc = Analysis.query.filter_by(xml_no=xml_no).first()
    file_path = acc.path
    
    if(acc == None):
        return DeleteResult.INVALID_PATH

    db.session.delete(acc)
    db.session.commit()
    acc = HostInfo.query.filter_by(no=acc.host_no).first()
    if(acc.analysis_count == 1):
        db.session.delete(acc)
    else:
        acc.analysis_count -= 1
        db.session.add(acc)
        
    db.session.commit()
    os.remove(UPLOAD_PATH + file_path)

    return DeleteResult.SUCCESS

def upload_file(fd):
    random_dir = time.strftime("%y%m%d_%H%M%S")

    os.makedirs(UPLOAD_PATH+random_dir+"/", exist_ok=True) #make directory
    
    p = UPLOAD_PATH + random_dir + "/" + secure_filename(fd[0].filename) 
    abs_path = os.path.abspath(p)
    fd[0].save(abs_path)
    return random_dir + "/" + secure_filename(fd[0].filename)

def insert_db(upload_time,  path, safe, vuln, host_name, ip, types):
    current_user = get_jwt_identity()
    acc = User.query.filter_by(id=current_user["user_id"]).first()
    for i in range(len(path)):
        an = Analysis.query.filter_by(path=path[i]).first()
        if(an != None):
            return UploadResult.INVALID_PATH
        an = HostInfo.query.filter_by(ip=ip, project_no=current_user["project_no"]).first()
        if (an == None):
            an = HostInfo(project_no=current_user["project_no"], host_name=host_name, analysis_count=1, timestamp=upload_time, types=types, ip=ip)
        else:
            an.analysis_count += 1
            an.timestamp = upload_time
        db.session.add(an)
        host = HostInfo.query.filter_by(ip=ip).first()
        host_no = host.no
        an = Analysis(upload_time=upload_time, project_no=current_user["project_no"], user_no=acc.user_no, path=path[i], safe=safe[i], vuln=vuln[i], host_no=host_no)
        db.session.add(an)
        db.session.commit()

    return UploadResult.SUCCESS    

def make_xlsx(xml_no):
    xml_no = xml_no.split("_")
    if(xml_no==['']):
        return XlsxResult.NO_ARGS, None
    xlsx_file = "analysis_result_" + time.strftime("%y%m%d_%H%M") + ".xlsx"
    with pd.ExcelWriter(UPLOAD_PATH + xlsx_file, engine='xlsxwriter') as writer:
        #for xml in xml_no:
        rows = []
        for i in range(len(xml_no)):
            parsed = parse_xml(xml_no[i])
            if(parsed == ParseResult.INVALID_FILE):
                return XlsxResult.INVALID_FILE, ''
            if(type(parsed)==type({})):
                xml_result = []
                an = Analysis.query.filter_by(xml_no=xml_no[i]).first()
                ho = HostInfo.query.filter_by(no=an.host_no).first()
            df_cols = ['No', 'Host_Name', 'IPaddress', 'OSVersion', 'group_name', 'title_name', 'important', 'decision', 'issue']

            for j in range(len(parsed["group_code"])):
                rows.append([i+1, ho.host_name, ho.ip, ho.types, parsed["group_name"][j], parsed["title_name"][j], parsed["important"][j], parsed["decision"][j], parsed["issue"][j]])

        df = pd.DataFrame(rows, columns = df_cols)
        xml_row = Analysis.query.filter_by(xml_no=xml_no[i]).first()
        file_name = xml_row.path
        df.to_excel(writer, index=False)
    return XlsxResult.SUCCESS, UPLOAD_PATH + xlsx_file

def get_hosts(project_no):
    host_list = HostInfo.query.filter_by(project_no=project_no).all()
    host_list_result = []
    for host in host_list:
        tmp = {}
        tmp["no"] = host.no
        tmp["host_name"] = host.host_name
        tmp["analysis_count"] = host.analysis_count
        tmp["timestamp"] = host.timestamp
        tmp["type"] = host.types
        tmp["ip"] = host.ip
        host_list_result.append(tmp)
    return host_list_result

def get_host_analysis(host_no):
    analysis_list = Analysis.query.filter_by(host_no=host_no).all()
    analysis_list_result = []
    for analysis in analysis_list:
        tmp = {}
        tmp["no"] = analysis.xml_no
        tmp["timestamp"] = analysis.upload_time
        tmp["path"] = analysis.path
        tmp["safe"] = analysis.safe
        tmp["vuln"] = analysis.vuln
        analysis_list_result.append(tmp)
    return analysis_list_result

def get_project_analysis():
    cur_user = get_jwt_identity()
    
    analysis_rows = Analysis.query.filter_by(project_no=cur_user['project_no']).order_by(Analysis.upload_time.desc()).all()
    analysis_list_result=[]
    for i in range(0,len(analysis_rows)):
        host_row = HostInfo.query.filter_by(no=analysis_rows[i].host_no).first()
        if(i==30):
            break
        tmp = {}
        tmp["xml_no"] = analysis_rows[i].xml_no
        tmp["upload_time"] = analysis_rows[i].upload_time
        tmp["project_no"] = analysis_rows[i].project_no
        tmp["host_name"] = host_row.host_name
        tmp["safe"] = analysis_rows[i].safe
        tmp["vuln"] = analysis_rows[i].vuln
        tmp["host_no"] = analysis_rows[i].host_no
        analysis_list_result.append(tmp)
    return analysis_list_result

def get_comments(xml_no, title_code):
    cur_user = get_jwt_identity()
    analysis_res = Analysis.query.filter_by(xml_no=xml_no).first()
    if(analysis_res == None or cur_user["project_no"] != analysis_res.project_no):
        return CommentingResult.INVALID_PROJECT_NO, ''
    comments = Comment.query.filter_by(xml_no=xml_no, title_code=title_code).order_by(Comment.timestamp.desc()).all()
    if(comments == None):
        return CommentingResult.NOCOMMENT, ''
    
    comment_list = []
    for comment in comments:
        tmp = {}
        tmp["no"] = comment.comment_no
        tmp["old_vuln"] = comment.old_vuln
        tmp["new_vuln"] = comment.new_vuln
        tmp["comment"] = comment.comment
        tmp["timestamp"] = comment.timestamp
        tmp["modifier"] = comment.modifier
        comment_list.append(tmp)

    return CommentingResult.SUCCESS, comment_list


def commenting(xml_no, title_code, comment, vuln):
    cur_user = get_jwt_identity()
    analysis_res = Analysis.query.filter_by(xml_no=xml_no).first()
    if(analysis_res == None or cur_user["project_no"] != analysis_res.project_no):
        return CommentingResult.INVALID_PROJECT_NO
    if(comment == None):
        return CommentingResult.NOCOMMENT
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    result, prev = patch_vuln(xml_no, title_code, vuln)
    comments = Comment.query.filter_by(xml_no=xml_no, title_code=title_code).order_by(Comment.comment_no.desc()).first()
    
    if(comments == None):
        comments = Comment(xml_no=xml_no, title_code=title_code, old_vuln=prev, new_vuln=vuln, comment=comment, timestamp=timestamp, modifier=cur_user["user_id"])
    else:
        comments = Comment(xml_no=xml_no, title_code=title_code, old_vuln=comments.new_vuln, new_vuln=vuln, comment=comment, timestamp=timestamp, modifier=cur_user["user_id"])
    
    if(result == CommentingResult.INVALID_FILE):
        return CommentingResult.INVALID_FILE
    elif(result == CommentingResult.WRITE_FAIL):
        return CommentingResult.WRITE_FAIL
    elif(result == CommentingResult.INVALID_DECISION):
        return CommentingResult.INVALID_DECISION
    elif(result == CommentingResult.SUCCESS):
        db.session.add(comments)
        db.session.commit()
        return CommentingResult.SUCCESS
    else:
        return ''

def patch_vuln(xml_no, title_code, vuln):
    if vuln not in ALLOWED_DECISION:
        return CommentingResult.INVALID_DECISION
    path = "uploads/"
    an = Analysis.query.filter_by(xml_no=xml_no).first()
    encoding = XMLParser(encoding='utf-8')
    try:
        tree = parse(path + an.path, parser=encoding)
    except:
        return CommentingResult.INVALID_FILE
    
    root = tree.getroot()
    row = root.findall("row")
    code = [x.findtext("Title_Code") for x in row]

    for i in range(len(code)):
        if(code[i] == title_code):
            prev = row[i][5].text
            row[i][5].text = vuln
    try:
        tree.write(path + an.path, encoding='utf-8')
    except:
        return CommentingResult.WRITE_FAIL
     
    an = Analysis.query.filter_by(xml_no=xml_no).first()
    if(prev == '양호'):
        an.safe -= 1
        if(vuln == '취약'):
            an.vuln += 1
        elif(vuln == '양호'):
            an.safe += 1
    elif(prev == '취약'):
        an.vuln -= 1
        if(vuln == '양호'):
            an.safe += 1
        elif(vuln == '취약'):
            an.vuln += 1
    db.session.add(an)
    db.session.commit()
    return CommentingResult.SUCCESS, prev

def delete_comment(comment_no):
    path = "uploads/"
    cur_user = get_jwt_identity()

    co = Comment.query.filter_by(comment_no=comment_no).first()
    tmp = Comment.query.filter_by(xml_no=co.xml_no).order_by(Comment.comment_no.desc()).first()
    if(co == None):
        return CommentingResult.INVALID_COMMENT
    an = Analysis.query.filter_by(xml_no=co.xml_no).first()
    if(an == None):
        return CommentingResult.INVALID_XML
    elif(an.project_no != cur_user["project_no"]):
        return CommentingResult.INVALID_PROJECT_NO
    
    if(co.comment_no == tmp.comment_no):
        encoding = XMLParser(encoding='utf-8')
        try:
            tree = parse(path + an.path, parser=encoding)
        except:
            return CommentingResult.INVALID_FILE
        
        root = tree.getroot()
        row = root.findall("row")
        code = [x.findtext("Title_Code") for x in row]

        for i in range(len(code)):
            if(code[i] == co.title_code):
                row[i][5].text = co.old_vuln
        try:
            tree.write(path + an.path, encoding='utf-8')
        except:
            return CommentingResult.WRITE_FAIL

        if(co.new_vuln == "양호"):
            an.safe -= 1
            if(co.old_vuln == '취약'):
                an.vuln += 1
            elif(co.old_vuln == '양호'):
                an.safe += 1
        elif(co.new_vuln == '취약'):
            an.vuln -= 1
            if(co.old_vuln == '양호'):
                an.safe += 1
            elif(co.old_vuln == '취약'):
                an.vuln += 1
        db.session.add(an)
    db.session.delete(co)
    db.session.commit()

    return CommentingResult.SUCCESS

def patch_comment(comment, comment_no):
    path = "uploads/"
    cur_user = get_jwt_identity()

    co = Comment.query.filter_by(comment_no=comment_no).first()
    if(co == None):
        return CommentingResult.INVALID_COMMENT
    an = Analysis.query.filter_by(xml_no=co.xml_no).first()
    if(an == None):
        return CommentingResult.INVALID_XML
    elif(an.project_no != cur_user["project_no"]):
        return CommentingResult.INVALID_PROJECT_NO

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    co.comment = comment
    co.timestamp = timestamp
    co.modifier = cur_user["user_id"]

    db.session.add(co)
    db.session.commit()

    return CommentingResult.SUCCESS

def modify_host_name(host_no, host_name, ip, types):
    cur_user = get_jwt_identity()
    host_res = HostInfo.query.filter_by(no = host_no).first()
    if(host_res == None or cur_user["project_no"] != host_res.project_no):
        return HostInfoResult.INVALID_HOST
    if(host_name != ''):
        host_res.host_name = host_name
    if(ip != ''):
        host_res.ip = ip
    if(types != ''):
        host_res.types = types
    db.session.add(host_res)
    db.session.commit()
    return HostInfoResult.SUCCESS
