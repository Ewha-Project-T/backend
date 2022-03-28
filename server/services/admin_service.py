from .login_service import DeleteResult
from ..model import User,Script
from server import db
import hashlib
import base64

class InitResult:
    SUCCESS = 0
    INVALID_USER_NO = 1
class UserChangeResult:
    SUCCESS = 0
    DUPLICATED_EMAIL = 1
    INVALID_USER = 2

def get_users_info():
    acc_list = User.query.all()
    info_list = []
    for info in acc_list:
        tmp_info = {}
        tmp_info["project_no"] = info.project_no
        tmp_info["user_no"] = info.user_no
        tmp_info["id"] = info.id
        tmp_info["permission"] = info.permission
        tmp_info["name"] = info.name
        tmp_info["email"] = info.email
        tmp_info["login_fail"] = info.login_fail_limit
        info_list.append(tmp_info)
    return info_list

def init_user_limit(user_no):
    acc = User.query.filter_by(user_no=user_no).first()
    if(acc==None):
        return InitResult.INVALID_USER_NO
    acc.login_fail_limit = 0
    db.session.add(acc)
    db.session.commit()
    return InitResult.SUCCESS

def delete_user(user_no):
    acc = User.query.filter_by(user_no=user_no).first()
    if(acc==None):
        return DeleteResult.INVALID_ID
    db.session.delete(acc)
    db.session.commit
    return DeleteResult.SUCCESS

def all_script_listing():
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

def patch_user(user_no,new_pw,email,name):
    if(email != None):
        email_check = User.query.filter_by(email=email).first()
        if(email_check != None):
            return UserChangeResult.DUPLICATED_EMAIL
    acc = User.query.filter_by(user_no=user_no).first()
    if(acc == None):
        return UserChangeResult.INVALID_USER
    if(new_pw!=None):
        password = base64.b64decode(acc.password)
        salt = password[:32]
        new_pw = base64.b64encode(salt + hashlib.pbkdf2_hmac('sha256', new_pw.encode('utf-8'), salt, 100000, dklen=128))
        acc.password = new_pw
    if(name != None):
        acc.name = name
    db.session.add(acc)
    db.session.commit()
    return UserChangeResult.SUCCESS