from ..model import User, Lecture
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity



def lecture_listing():
    lecture_list=Lecture.query.all()
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
    acc=Lecture(lecture_name=name,year=year,semester=semester,major=major,separated=separated,professor=professor)
    db.session.add(acc)
    db.session.commit

def modify_lecture(no,name,year,semester,major,separated,professor):
    acc=Lecture.query.filter_by(lecture_no=no).first()
    acc.name=name
    acc.year=year
    acc.semester=semester
    acc.major=major
    acc.separated=separated
    acc.professor=professor
    db.session.add(acc)
    db.session.commit()

def delete_lecture(lecture_no):
    acc = Lecture.query.filter_by(lecture_no=lecture_no).first()
    db.session.delete(acc)
    db.session.commit

def search_student(name,major):
    acc=User.query.filter_by(name=name,major=major).all()
    student_list_result=[]
    for user in acc:
        tmp={}
        tmp["user_no"]=vars(user)["user_no"]
        tmp["email"]=vars(user)["email"]
        tmp["name"]=vars(user)["name"]
        tmp["major"]=vars(user)["major"]
        tmp["permission"]=vars(user)["permission"]
        student_list_result.append(tmp)
    return student_list_result

