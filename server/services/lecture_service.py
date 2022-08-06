from ..model import User, Lecture
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity



def lecture_listing(user_no):
    lecture_list=Lecture.query.filter_by(user_no=user_no).all()
    lecture_list_result=[]
    for lec in lecture_list:
        tmp={}
        tmp["lecture_no"]=vars(lec)["lecture_no"]
        tmp["lecture_name"]=vars(lec)["lecture_name"]
        tmp["year"]=vars(lec)["year"]
        tmp["semester"]=vars(lec)["semester"]
        tmp["major"]=vars(lec)["major"]
        tmp["separated"]=vars(lec)["separated"]
        tmp["professor"]=vars(lec)["professor"]
        lecture_list_result.append(tmp)
    return lecture_list_result

def make_lecture(name,year,semester,major,separated,professor):
    userinfo = get_jwt_identity()
    acc=Lecture(lecture_name=name,year=year,semester=semester,major=major,separated=separated,professor=professor,user_no=userinfo["user_no"])
    db.session.add(acc)
    db.session.commit
