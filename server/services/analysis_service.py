import zipfile
import tarfile
import os

ALLOWED_EXTENSIONS = set(['zip', 'xml','tar'])



def compression_extract(file_path, ext, save_path="./"):

    os.makedirs(file_path + "random_", exist_ok=True)
    
    if ext == "zip":
        f = zipfile.ZipFile(file_path)
    elif ext == "tar":
        f = tarfile.open(file_path)
                
    f.extractall(save_path) 
    f.close()


def get_file_ext(filename):
    if '.' in filename:
        if filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS:
            return filename.rsplit('.',1)[1]
    return ''
