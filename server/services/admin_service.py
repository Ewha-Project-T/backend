from .login_service import DeleteResult
from ..model import User
from server import db
import hashlib
import base64



def get_users_info(proj_no=None):
    if(proj_no==None):
        acc_list = User.query.all()
    else:
        acc_list = User.query.filter_by(project_no=proj_no).all()
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




