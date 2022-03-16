from ..model import User
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
import hashlib
import base64

class LoginResult:
    SUCCESS = 0
    INVALID_IDPW = 1
    LOGIN_COUNT_EXCEEDED=2
    INTERNAL_ERROR = 3

class RegisterResult:
    SUCCESS = 0
    INVALID_IDPW = 1
    USERID_EXIST = 2
    USEREMAIL_EXIST = 3

class DeleteResult:
    SUCCESS = 0
    INVALID_ID = 1
    PW_NOT_MATCHED = 2
    INVALID_EMAIL = 3
    
class ChangeResult:
    SUCCESS = 0
    INVALID_PW = 1
    INCORRECT_PW = 2
    INVALID_EMAIL = 3
    INVALID_NAME = 4

def login(user_id, user_pw):
    acc = User.query.filter_by(id=user_id).first()
    passwd = base64.b64decode(acc.password)
    salt = passwd[:32]
    encrypt_pw = hashlib.pbkdf2_hmac('sha256', user_pw.encode('utf-8'), salt, 100000, dklen=128)
    if(acc.login_fail_limit>=5):
        return LoginResult.LOGIN_COUNT_EXCEEDED, acc
    if(acc!=None and encrypt_pw==passwd[32:]):
        acc.login_fail_limit=0
        db.session.commit
        return LoginResult.SUCCESS, acc
    acc.login_fail_limit+=1
    db.session.commit
    return LoginResult.INVALID_IDPW, acc

def create_tokens(user: User, **kwargs):
    identities = {
        "type": "login",
        "user_id": user.id,
        "user_name": user.name,
        "user_perm": user.permission
    }
    return create_access_token(identities, **kwargs), create_refresh_token(identities, **kwargs)

def register(user_id,user_pw,user_name,user_email):
    if(len(user_id)<4 or len(user_id)>20 or len(user_pw)<4 or len(user_pw)>20): #아이디 비번 글자수제한
        return RegisterResult.INVALID_IDPW
    acc = User.query.filter_by(id=user_id).first()
    if acc !=None:
        return RegisterResult.USERID_EXIST
    acc = User.query.filter_by(email=user_email).first()
    if acc !=None:
        return RegisterResult.USEREMAIL_EXIST

    acc=User(id=user_id,password=user_pw,name=user_name,email=user_email)
    db.session.add(acc)
    db.session.commit
    return RegisterResult.SUCCESS


def delete(user_id):
    acc = User.query.filter_by(id=user_id).first()
    if(acc==None):
        return DeleteResult.INVALID_ID
    db.session.delete(acc)
    db.session.commit
    return DeleteResult.SUCCESS

def change(old_pw, new_pw, new_name, new_email):
    userinfo = get_jwt_identity()
    if(userinfo==None):
        raise Exception("Not Logged In")
    acc = User.query.filter_by(id=userinfo["user_id"]).first()
    if(old_pw != None and new_pw != None):
        password = base64.b64decode(acc.password)
        salt = password[:32]
        old_pw = hashlib.pbkdf2_hmac('sha256', old_pw.encode('utf-8'), salt, 100000, dklen=128)
        if(old_pw != password[32:]):
            return ChangeResult.INCORRECT_PW
        new_pw = base64.b64encode(salt + hashlib.pbkdf2_hmac('sha256', new_pw.encode('utf-8'), salt, 100000, dklen=128))
        acc.password = new_pw
    if(new_name != None):
        acc.name = new_name
    if(new_email != None):
        acc.email = new_email
    db.session.add(acc)
    db.session.commit()
    return ChangeResult.SUCCESS

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            print(claims)
            if(claims["sub"]["user_perm"]==2):
                return fn(*args, **kwargs)
            else:
                return {"msg":"admin only"}, 403

        return decorator

    return wrapper

