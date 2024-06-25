from ..model import User, Lecture
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
import hashlib
import base64
import os

class LoginResult:
    SUCCESS = 0
    INVALID_EMAILPW = 1
    LOGIN_COUNT_EXCEEDED=2
    ACC_IS_NOT_FOUND = 3
    NEED_EMAIL_CHECK = 4
    NEED_ADMIN_CHECK = 5
    INTERNAL_ERROR = 6
    
class RegisterResult:
    SUCCESS = 0
    USEREMAIL_EXIST = 1
    INVALID_PERM = 2


def login(user_email, user_pw):#로그인
    acc = User.query.filter_by(email=user_email).first()
    if(acc == None):
        return LoginResult.ACC_IS_NOT_FOUND, acc
    passwd = base64.b64decode(acc.password)
    salt = passwd[:32]
    encrypt_pw = hashlib.pbkdf2_hmac('sha256', user_pw.encode('utf-8'), salt, 100000, dklen=128)
    if(encrypt_pw==passwd[32:]):
        if(acc.access_check==0):
            return LoginResult.NEED_EMAIL_CHECK, acc
        return LoginResult.SUCCESS, acc
    return LoginResult.INVALID_EMAILPW, acc

def create_tokens(user: User, **kwargs):#jwt토큰 생성
    identities = {
        "type": "login",
        "user_no": user.user_no,
        "user_email": user.email,
        "user_name": user.name,
        "user_major": user.major,
        "user_perm": user.permission,
    }
    return create_access_token(identities, **kwargs), create_refresh_token(identities, **kwargs)

def register(user_email,user_pw,user_name,user_major, user_perm):#유저생성 
    acc = User.query.filter_by(email=user_email).first()
    if acc !=None:
        return RegisterResult.USEREMAIL_EXIST
    if(user_perm>3 or user_perm<0):
        return RegisterResult.INVALID_PERM
    acc=User(email=user_email,password=user_pw,name=user_name,major=user_major,permission=user_perm)#,user_identifier=user_ident) 학번이나 자신만의 문자를 입력하라 해야할듯(아이디찾기용)
    db.session.add(acc)
    db.session.commit
    return RegisterResult.SUCCESS

def real_time_email_check(user_email):#회원가입시 이메일 중복 체크
    acc = User.query.filter_by(email=user_email).first()
    if acc !=None:
        return RegisterResult.USEREMAIL_EXIST
    return 0
def get_all_user():#학생계정 전체조회
    acc_list = User.query.all()
    info_list = []
    for info in acc_list:#교수와 관리자계정은 제외했음
        if vars(info)["permission"]==3 or vars(info)["permission"]==0:
            continue
        tmp_info = {}
        tmp_info["email"] = info.email
        tmp_info["name"] = info.name
        tmp_info["major"] = info.major
        info_list.append(tmp_info)
    return info_list


def admin_required(): #관리자 권한
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if(claims["sub"]["user_perm"]==0):
                return fn(*args, **kwargs)
            else:
                return {"msg":"admin only"}, 403

        return decorator

    return wrapper

def findpassword_email_check(user_email):#비밀번호찾기 이메일 존재여부 확인
    acc = User.query.filter_by(email=user_email).first()
    if acc ==None:
        return 0
    return 1

def findpassword_code_check(email,code):#비밀번호찾기 코드일치 확인
    acc = User.query.filter_by(email=email).first()
    if acc ==None:
        return 0
    if(acc.access_code!=code):
        return 0
    return 1
def encrypt_password(password):#패스워드 암호화
    salt = os.urandom(32)
    encrypt_passwd = base64.b64encode(salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=128))
    return encrypt_passwd
def change_pass(email,password):#비밀번호 변경
    acc = User.query.filter_by(email=email).first()
    acc.password=encrypt_password(password)
    db.session.commit()
def find_id(name, major, permission):#아이디 찾기->아이디중 일부를 마스킹하여 전달
    results = []
    acc = User.query.filter_by(name=name, major=major, permission=permission).all()
    if not acc:
        return 0
    num=0
    for user in acc:
        user_info = {
            "idx": num,
            "email": mask_email(user.email)
        }
        results.append(user_info)
        num+=1
    return results


def mask_email(email):#아이디 찾기에 보여지는 이메일 마스킹
    user_name, domain = email.split('@')
    if len(user_name) > 4:
        user_name_masked = user_name[:2] + '*' * (len(user_name) - 4) + user_name[-2:]
    else:
        user_name_masked = user_name[0] + '*' * (len(user_name) - 2) + user_name[-1] if len(user_name) > 1 else user_name + '*'
    return user_name_masked + '@' + domain





