import zipfile
import tarfile
import os
import time
import shutil
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = set(['zip', 'xml','tar'])

UPLOAD_PATH ='../../uploads/'

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
            return filename.rsplit('.',1)[1]
    return ''

def delete_analysis_file(file_path):
    folder_path = os.path.dirname(file_path)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        
    return ''

def upload_file(fd):
    random_dir = time.strftime("%Y%m%d_%H%M%S")[2:]

    os.makedirs(UPLOAD_PATH+random_dir+"/", exist_ok=True) #make directory
    
    p = UPLOAD_PATH + random_dir + "/" +  secure_filename(fd.filename) 
    abs_path = os.path.abspath(p)
    fd.save(abs_path)

    return abs_path