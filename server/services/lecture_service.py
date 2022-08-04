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
        tmp["boss"]=vars(lec)["boss"]
        lecture_list_result.append(tmp)
    return lecture_list_result
    
    이프로젝트는 다수유저가 하나의 프로젝트를 가지고있음 
    만드느건 프로젝트가 유저를 가지고 있어야함 강의목록 조회시 프로젝트들중 user_no가 목표값인 사람을 찾아야함 
