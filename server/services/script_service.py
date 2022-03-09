from ..model import Script

def fileDownload(file_name):
    file_path = "../../script_files/"+file_name
    f = open(file_path, "rt")
    data = f.read()
    return data




