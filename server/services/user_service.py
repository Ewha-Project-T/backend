from server import db
from ..model import User

def get_user_by_id(user_id:int):
    user = db.session.query(User).filter(User.user_no == user_id).first()
    return {"name" : user.name,
            "major" : user.major,
            "email" : user.email, 
            "permission" : user.permission
            }
    