from unittest import registerResult
from ..model import User
from server import db

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

# def is_exist(column_name, value):
#     user = User.query.filter(column_name==value).first()
#     return user != None

def login(user_id, user_pw):
    acc = User.query.filter_by(id=user_id).first()
    if(acc!=None and user_pw==acc.password):
        return LoginResult.SUCCESS, acc
    return LoginResult.INVALID_IDPW, acc

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


def delete(user_id):
    acc= User.query.filter_by(id=user_id).first()
    if(acc==None):
        return DeleteResult.INVALID_ID
    db.session.delete(acc)
    db.session.commit
    return DeleteResult.SUCCESS


