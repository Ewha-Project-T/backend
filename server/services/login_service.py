import email
from ..model import User, Lecture
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
import hashlib
import base64

class LoginResult:
    SUCCESS = 0
    INVALID_EMAILPW = 1
    LOGIN_COUNT_EXCEEDED=2
    ACC_IS_NOT_FOUND = 3
    NEED_ADMIN_CHECK = 4
    INTERNAL_ERROR = 5
    
class RegisterResult:
    SUCCESS = 0
    USEREMAIL_EXIST = 1
    INVALID_PERM = 2


def login(user_email, user_pw):
    acc = User.query.filter_by(email=user_email).first()
    if(acc == None):
        return LoginResult.ACC_IS_NOT_FOUND, acc
    if(acc.access_check==0):
        return LoginResult.NEED_ADMIN_CHECK, acc
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
    return LoginResult.INVALID_EMAILPW, acc

def create_tokens(user: User, **kwargs):
    identities = {
        "type": "login",
        "user_no": user.user_no,
        "user_email": user.email,
        "user_name": user.name,
        "user_major": user.major,
        "user_perm": user.permission,
    }
    return create_access_token(identities, **kwargs), create_refresh_token(identities, **kwargs)

def register(user_email,user_pw,user_name,user_major, user_perm): 
    

    acc = User.query.filter_by(email=user_email).first()
    if acc !=None:
        return RegisterResult.USEREMAIL_EXIST
    if(user_perm>3 or user_perm<0):
        return RegisterResult.INVALID_PERM
    acc=User(email=user_email,password=user_pw,name=user_name,major=user_major,permission=user_perm)
    db.session.add(acc)
    db.session.commit
    return RegisterResult.SUCCESS


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

def professor_required():#교수권한
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if(claims["sub"]["user_perm"]>=3 or claims["sub"]["user_perm"]==0):
                return fn(*args, **kwargs)
            else:
                return {"msg":"professor only"}, 403

        return decorator

    return wrapper

def assistant_required():#조교권한
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if(claims["sub"]["user_perm"]>=2 or claims["sub"]["user_perm"]==0):
                return fn(*args, **kwargs)
            else:
                return {"msg":"assistant only"}, 403

        return decorator

    return wrapper

