import zipfile
import tarfile
import os
import time
import shutil
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
from werkzeug.utils import secure_filename
from server import db
from ..model import User, Analysis, HostInfo
from ..services.xml_parser import parse_xml, ParseResult
import pandas as pd
import xlsxwriter
from flask import send_file

ALLOWED_EXTENSIONS = set(['zip', 'xml','tar'])
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

def insert_db(upload_time,  path, safe, vuln):
    current_user = get_jwt_identity()
    acc = User.query.filter_by(id=current_user["user_id"]).first()
    comment = ''
    for i in range(len(path)):
        an = Analysis.query.filter_by(path=path[i]).first()
        if(an != None):
            return UploadResult.INVALID_PATH
        host_name='_'.join(path[i].split("/")[1].split('_')[:-1])
        types=path[i].split("/")[1].split('_')[1]    
        ip = '.'.join(path[i].split("/")[1].split("_")[-1].split(".")[:-1])
        an = HostInfo.query.filter_by(ip=ip).first()
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
        db.session.commit

    return UploadResult.SUCCESS    

def make_xlsx(xml_no):
    parsed = parse_xml(xml_no)

    if(type(parsed)==type({})):
        xml_result = []
        for i in range(len(parsed["group_code"])):
            xml_result.append({
                'group_code' : parsed["group_code"][i],
                'group_name' : parsed["group_name"][i],
                'title_code' : parsed["title_code"][i],
                'title_name' : parsed["title_name"][i],
                'important' : parsed["important"][i],
                'decision' : parsed["decision"][i],
                'issue' : parsed["issue"][i], 
                'code' : parsed["codes"][i]})
    print(xml_result)
    df_cols = ['group_code', 'group_name', 'title_code', 'title_name', 'important', 'decision', 'issue', 'code']
    rows = []
    for i in range(len(parsed["group_code"])):
        rows.append([parsed["group_code"][i], parsed["group_name"][i], parsed["title_code"][i], parsed["title_name"][i], parsed["important"][i], parsed["decision"][i], parsed["issue"][i], parsed["codes"][i]])
    df = pd.DataFrame(rows, columns = df_cols)

    xml_row = Analysis.query.filter_by(xml_no=xml_no).first()
    file_name = xml_row.path
    xlsx_file = "analysis_result_" + time.strftime("%y%m%d_%H%M") + ".xlsx"
    with pd.ExcelWriter(UPLOAD_PATH + xlsx_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='_'.join(file_name.split("/")[1].split('_')[:-1]))
    return UPLOAD_PATH + xlsx_file
    #return UploadResult.SUCCESS 

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
    rows = Analysis.query.filter_by(project_no=cur_user['project_no']).all()
    analysis_list_result=[]
    for i in range(0,len(rows)):
        if(i==30):
            break
        tmp = {}
        tmp["upload_time"] = rows[i].upload_time
        tmp["project_no"] = rows[i].project_no
        tmp["host_name"] = '_'.join(rows[i].path.split("/")[1].split('_')[:-1])
        tmp["comment"] = rows[i].comment
        tmp["safe"] = rows[i].safe
        tmp["vuln"] = rows[i].vuln
        tmp["host_no"] = rows[i].host_no
        analysis_list_result.append(tmp)
    return analysis_list_result
    