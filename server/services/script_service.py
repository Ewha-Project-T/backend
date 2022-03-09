from ..model import Script

def fileDownload(file_name):
    acc = Script.query.filter_by(script_name=file_name)
    
    if acc != "":
        file_path = "../../script_files/"+file_name
        f = open(file_path, "rt")   
        return f.read()     

    else:
        return {'msg':'파일을 찾을 수 없습니다'}




