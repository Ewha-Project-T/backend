import zipfile
import tarfile
import os
import time
import shutil
from werkzeug.utils import secure_filename
from server import db
from ..model import Analysis, HostInfo
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

def delete_analysis_file(file_path):
    '''
    folder_path = os.path.dirname(file_path)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    '''
    acc = Analysis.query.filter_by(path=file_path).first()
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

def insert_db(upload_time, project_no, user_no, path, safe, vuln):
    comment = ''
    for i in range(len(path)):
        acc = Analysis.query.filter_by(path=path[i]).first()
        if(acc != None):
            return UploadResult.INVALID_PATH
        host_name='_'.join(path[i].split("/")[1].split('_')[:-1])
        types=path[i].split("/")[1].split('_')[1]    
        ip = '.'.join(path[i].split("/")[1].split("_")[-1].split(".")[:-1])
        acc = HostInfo.query.filter_by(ip=ip).first()
        if (acc == None):
            acc = HostInfo(project_no=project_no, host_name=host_name, analysis_count=1, timestamp=upload_time, types=types, ip=ip)
        else:
            acc.analysis_count += 1
            acc.timestamp = upload_time
        db.session.add(acc)
        acc = HostInfo.query.filter_by(ip=ip).first()
        host_no = acc.no
        acc = Analysis(upload_time=upload_time, project_no=project_no, user_no=user_no, path=path[i], safe=safe[i], vuln=vuln[i], host_no=host_no)
        db.session.add(acc)
        db.session.commit

    return UploadResult.SUCCESS    

def make_xlsx(file_name):
    df_list = []
    '''
    print(files)
    for file_name in files:
        result, group_code, group_name, title_code, title_name, important, decision, issue, code = parse_xml(file_name)
        print(file_name)
        if(result != ParseResult.SUCCESS):
            return {'msg' : "INVALID FILE NAME"}, 400
        
        df_cols = ['group_code', 'group_name', 'title_code', 'title_name', 'important', 'decision', 'issue', 'code']
        rows = []
        for i in range(len(group_code)):
            rows.append([group_code[i], group_name[i], title_code[i], title_name[i], important[i], decision[i], issue[i], code[i]])
        
        df = pd.DataFrame(rows, columns = df_cols)
        print(df)
    
        df_list.append(df)
        
    xlsx_file = "analysis_result_" + time.strftime("%y%m%d_%H%M") + ".xlsx"
    with pd.ExcelWriter(xlsx_file, engine='xlsxwriter') as writer:
        for i in range(len(file_name)):
            df[i].to_excel(writer, sheet_name=file_name[i])
    '''
    result, group_code, group_name, title_code, title_name, important, decision, issue, code = parse_xml(file_name)
    
    if(result != ParseResult.SUCCESS):
        return {'msg' : "INVALID FILE NAME"}, 400
    
    df_cols = ['group_code', 'group_name', 'title_code', 'title_name', 'important', 'decision', 'issue', 'code']
    rows = []
    for i in range(len(group_code)):
        rows.append([group_code[i], group_name[i], title_code[i], title_name[i], important[i], decision[i], issue[i], code[i]])
    df = pd.DataFrame(rows, columns = df_cols)

    xlsx_file = "analysis_result_" + time.strftime("%y%m%d_%H%M") + ".xlsx"
    with pd.ExcelWriter(UPLOAD_PATH + xlsx_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='_'.join(file_name.split("/")[1].split('_')[:-1]))
    return UPLOAD_PATH + xlsx_file