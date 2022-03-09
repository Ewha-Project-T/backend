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
    # password 는 평문으로 프론트에서 입력하지만 filter_by 로 직접 걸러내지않음
    # verify_password 함수에서 SHA256 + SALT 를 통한 체크 해주어야 할 것
    if(acc!=None and acc.verify_password(user_pw)):
        return LoginResult.SUCCESS, acc
    return LoginResult.INVALID_IDPW, acc

