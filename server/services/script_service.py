from ..model import Script
from server import db
from datetime import datetime
from sqlalchemy import text
from sqlalchemy import select

class UploadResult:
    SUCCESS = 0 
    DUPLICATED_NAME = 1
    INVALID_EXTENSION = 2
    INTERNAL_ERROR = 3

def upload_formatter(file_name):
    now = datetime.now()
    current_time = now.strftime("%H_%M_%S")
    filename = ("-"+current_time+".").join(file_name.split("."))
    return filename
    
def upload_script(script_type, proj_no, file_name):
    file = Script.query.filter_by(script_name=file_name).first()
    if(file!=None):
        return UploadResult.DUPLICATED_NAME
    file = Script(type=script_type,project_no=proj_no, script_name=file_name)
    db.session.add(file)
    db.session.commit
    return UploadResult.SUCCESS

def script_listing():
    script_list = Script.query.all()
    script_list_result = []
    for script in script_list:
        tmp = {}
        tmp["id"] = vars(script)["id"]
        tmp["type"] = vars(script)["type"]
        tmp["project_no"] = vars(script)["project_no"]
        tmp["script_name"] = vars(script)["script_name"]
        script_list_result.append(tmp)
    return script_list_result


