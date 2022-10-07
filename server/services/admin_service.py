from ..model import User
from server import db
import hashlib
import base64

class AdminResult:
    SUCCESS = 0
    NOT_FOUND= 1

def user_listing(mode=None):#mode none일시 전체검색, 1일시 가입승인필요한 사람만 검색
    if(mode==None):
        acc_list = User.query.all()
    else:
        acc_list = User.query.filter_by(access_check=0).all()
    user_list = []
    for user in acc_list:
        tmp_uesr = {}
        tmp_uesr["user_no"] = user.user_no
        tmp_uesr["email"] = user.email
        tmp_uesr["name"] = user.name
        tmp_uesr["major"] = user.major
        tmp_uesr["permission"] = user.permission
        tmp_uesr["login_fail"] = user.login_fail_limit
        tmp_uesr["access_check"] = user.access_check
        user_list.append(tmp_uesr)
    if not user_list:
        return AdminResult.NOT_FOUND,user_list
    return AdminResult.SUCCESS,user_list

def activating_user(email):#일단기능만 에러처리는 나중에~
    acc= User.query.filter_by(email=email).first()
    acc.access_check=1
    db.session.add(acc)
    db.session.commit

def del_user(email):
    acc = User.query.filter_by(email=email).first()
    db.session.delete(acc)
    db.session.commit

def init_pass_cnt(email):
    acc = User.query.filter_by(email=email).first()
    acc.login_fail_limit=0
    db.session.add(acc)
    db.session.commit


