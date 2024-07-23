from server import db
from ..model import User

def get_user_by_id(user_id:int):
    user = db.session.query(User).filter(User.user_no == user_id).first()
    return {"name" : user.name,
            "major" : user.major,
            "email" : user.email, 
            "permission" : user.permission
            }

def update_user(user_no:int, user_name:str, user_major:str):
    user = User.query.filter_by(user_no=user_no).first()
    user.name = user_name
    user.major = user_major
    db.session.commit()
    return {
        "name" : user.name,
        "major" : user.major,
        "email" : user.email,
        "isSuccess" : True,
        }
