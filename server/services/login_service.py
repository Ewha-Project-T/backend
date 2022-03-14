from unittest import registerResult
from ..model import User
from server import db
import functools
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
import hashlib
import os
import base64


class LoginResult:
    SUCCESS = 0
    INVALID_IDPW = 1
    INTERNAL_ERROR = 2

class RegisterResult:
    SUCCESS = 0
    INVALID_IDPW = 1
    USERID_EXIST = 2
    USEREMAIL_EXIST = 3
    #INTERNAL_ERROR = 4 #없어도 되지않을까 싶음

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
    key = base64.b64decode(acc.password)
    salt = key[:32]
    encrypt_pw = hashlib.pbkdf2_hmac('sha256', user_pw.encode('utf-8'), salt, 100000, dklen=128)
    if(acc!=None and encrypt_pw==key[32:]):
        return LoginResult.SUCCESS, acc
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

    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', user_pw.encode('utf-8'), salt, 100000, dklen=128)
    encrypt_pw = salt + key # [:32] = salt, [32:] = key
    encrypt_pw = base64.b64encode(encrypt_pw)

    acc=User(id=user_id,password=encrypt_pw,name=user_name,email=user_email)
    #acc=User(id=user_id,password=user_pw,name=user_name,email=user_email)
    db.session.add(acc)
    db.session.commit
    return RegisterResult.SUCCESS


def delete(user_id):
    acc = User.query.filter_by(id=user_id).first()
    print(acc)
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
        # * old_pw 해시 한 것과 DB 내용과 비교해야함.
        if(old_pw != acc.password):
            return ChangeResult.INCORRECT_PW
        acc.password = new_pw
    if(new_name != None):
        acc.name = new_name
    if(new_email != None):
        acc.email = new_email
    db.session.add(acc)
    db.session.commit()
    return ChangeResult.SUCCESS

def login_required():
    def wrapper(func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if(claims == None):
                    return {'msg':'로그인이 필요합니다.'}, 401
                return func(*args, **kwargs)
            except:
                return {'msg':'유효하지 않은 토큰입니다.'}, 403
        return decorator
    return wrapper


