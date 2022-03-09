from unittest import registerResult
from ..model import User
from server import db
import functools
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt

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

# def is_exist(column_name, value):
#     user = User.query.filter(column_name==value).first()
#     return user != None

def login(user_id, user_pw):
    acc = User.query.filter_by(id=user_id).first()
    if(acc!=None and user_pw==acc.password):
        return LoginResult.SUCCESS, acc
    return LoginResult.INVALID_IDPW, acc
def create_tokens(user: User):
    identities = {
        "type": "login",
        "user_id": user.id,
        "user_name": user.name,
        "user_perm": user.permission
    }
    return create_access_token(identities), create_refresh_token(identities)

def register(user_id,user_pw,user_name,user_email):
    if(len(user_id)<4 or len(user_id)>20 or len(user_pw)<4 or len(user_pw)>20):#아이디 비번 글자수제한
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


def delete(user_id,user_pw,user_name,user_email):
    acc=User(id=user_id,password=user_pw,name=user_name,email=user_email)
    db.session.delete(acc)
    db.session.commit

def login_required():
    def wrapper(func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                print(claims)
                if claims == None:
                    return {'msg':'로그인이 필요합니다.'}, 401
                return func(*args, **kwargs)
            except:
                return {'msg':'유효하지 않은 토큰입니다.'}, 403
        return decorator
    return wrapper


