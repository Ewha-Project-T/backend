from .login_service import DeleteResult
from ..model import User
from server import db

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

def delete_user(user_no):
    acc = User.query.filter_by(user_no=user_no).first()
    if(acc==None):
        return DeleteResult.INVALID_ID
    db.session.delete(acc)
    db.session.commit
    return DeleteResult.SUCCESS