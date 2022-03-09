from ..model import Script

def fileDownload(file_name):
    acc = Script.query.filter_by(file_name)
    
    file_path = "../../script_files/"+file_name
    f = open(file_path, "rt")   
    return f.read()




