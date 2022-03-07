from ..model import User

class LoginResult:
    SUCCESS = 0
    INVALID_IDPW = 1
    INTERNAL_ERROR = 2

class RegisterResult:
    SUCCESS = 0
    INVALID_IDPW = 1
    USERID_EXIST = 2
    USEREMAIL_EXIST = 3
    INTERNAL_ERROR = 4

# def is_exist(column_name, value):
#     user = User.query.filter(column_name==value).first()
#     return user != None

def login(user_id, user_pw):
    acc = User.query.filter_by(id=user_id).first()
    if(acc!=None and acc.verify_password(user_pw)):
        return LoginResult.SUCCESS, acc
    return LoginResult.INVALID_IDPW, acc

