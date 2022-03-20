import zipfile
import tarfile
import os
import time
import shutil
from werkzeug.utils import secure_filename
from server import db
from ..model import Analysis

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
        f = zipfile.ZipFile(file_path)
    elif ext == "tar":
        f = tarfile.open(file_path)

    f.extractall()
    
    os.remove(file_path)
    f.close()


def get_file_ext(filename):
    if '.' in filename:
        if filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS:
            return ExtensionsResult.SUCCESS, filename.rsplit('.',1)[1]
        else:
            return ExtensionsResult.DENIED_EXTENSIONS, ''
    return ''

def delete_analysis_file(file_path):
    folder_path = os.path.dirname(file_path)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        
    return ''

def upload_file(fd):
    random_dir = time.strftime("%y%m%d_%H%M%S")

    os.makedirs(UPLOAD_PATH+random_dir+"/", exist_ok=True) #make directory
    
    p = UPLOAD_PATH + random_dir + "/" + secure_filename(fd[0].filename) 
    abs_path = os.path.abspath(p)
    fd[0].save(abs_path)
    return random_dir + "/" + secure_filename(fd[0].filename) 

def insert_db(upload_time, project_no, user_no, path, safe, vuln):
    comment = ''
    acc = Analysis.query.filter_by(path=path).first()
    if(acc != None):
        return UploadResult.INVALID_PATH
    
    acc = Analysis(upload_time=upload_time, project_no=project_no, user_no=user_no, path=path, safe=safe, vuln=vuln)    
    #print(acc)
    db.session.add(acc)
    db.session.commit

    return UploadResult.SUCCESS