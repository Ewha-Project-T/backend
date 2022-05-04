from ..model import Script, Project, PROJECT_SCRIPT
from server import db
from datetime import datetime
from sqlalchemy import delete
import os

class UploadResult:
    SUCCESS = 0 
    DUPLICATED_NAME = 1
    INVALID_EXTENSION = 2
    INTERNAL_ERROR = 3
    INVALID_PROJECT_NO = 4

class DownloadAuthResult:
    SUCCESS = 0
    INVALID = 1

class DeleteResult:
    SUCCESS = 0
    FAIL = 1

def upload_formatter(file_name):
    now = datetime.now()
    current_time = now.strftime("%H_%M_%S")
    filename = ("-"+current_time+".").join(file_name.split("."))
    return filename
    
def upload_script(script_type, proj_no, file_name):
    proj = Project.query.filter_by(project_no=proj_no).first()
    if(proj == None):
        return UploadResult.INVALID_PROJECT_NO
    file = Script.query.filter_by(script_name=file_name).first()
    if(file!=None):
        return UploadResult.DUPLICATED_NAME
    file = Script(type=script_type,project_no=proj_no, script_name=file_name)
    db.session.add(file)
    db.session.commit
    return UploadResult.SUCCESS

def download_auth_check(file_name):
    file = Script.query.filter_by(script_name=file_name).first()
    if(file!=None):
        return DownloadAuthResult.SUCCESS
    else:
        return DownloadAuthResult.INVALID

def delete_script(file_name, file_path):
    os.remove(file_path)
    try:
        file = delete(Script).where(Script.script_name==file_name)
        db.session.execute(file)
        db.session.commit()
    except:
        return DeleteResult.FAIL
    else:
        return DeleteResult.SUCCESS


def script_listing(proj_no):
    script_list = PROJECT_SCRIPT.query.filter_by(project_no=proj_no).all()
    script_list_result = []
    for script in script_list:
        tmp = {}
        tmp["id"] = vars(script)["no"]
        tmp["type"] = vars(script)["type"]
        tmp["project_no"] = vars(script)["project_no"]
        tmp["script_name"] = vars(script)["script_name"]
        script_list_result.append(tmp)
    return script_list_result


