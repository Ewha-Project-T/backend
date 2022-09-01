from ..model import Attendee, User, Lecture
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
import json


def lecture_listing(user_no=None):
    lecture_list_result=[]
    if(user_no==None):#관리자용 전체조회
        lecture_list=Lecture.query.order_by(Lecture.lecture_no.desc()).all()
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
    else:
        attend=Attendee.query.filter_by(user_no=user_no["user_no"]).order_by(Attendee.attendee_no.desc()).all()#학생교수조교용
        for at in attend:
            lecture_list=Lecture.query.filter_by(lecture_no=at.lecture_no).all()
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

def make_lecture(name,year,semester,major,separated,professor,attendee,user_info):
    acc=Lecture(lecture_name=name,year=year,semester=semester,major=major,separated=separated,professor=professor)
    db.session.add(acc)
    db.session.commit
    this_lecture=Lecture.query.order_by(Lecture.lecture_no.desc()).first()
    professor_no=user_info["user_no"]
    professor=Attendee(user_no=professor_no,lecture_no=this_lecture.lecture_no,permission=3)
    db.session.add(professor)
    db.session.commit
    for attendee_user in attendee:
        attendee_user=attendee_user.replace("'",'"')
        user=json.loads(attendee_user)
        user_email=user["email"]
        user_name=user["name"]
        user_acc=User.query.filter_by(email=user_email,name=user_name).first()
        if user_acc==None:
            continue
        attend=Attendee(user_no=user_acc.user_no,lecture_no=this_lecture.lecture_no,permission=user_acc.permission)
        db.session.add(attend)
        db.session.commit


def modify_lecture(no,name,year,semester,major,separated,professor,attendee,user_info):
    acc=Lecture.query.filter_by(lecture_no=no).first()
    if name !="":
        acc.lecture_name=name
    if year !="":
        acc.year=year
    if semester !="":
        acc.semester=semester
    if major !="":
        acc.major=major
    if separated !="":
        acc.separated=separated
    if professor !="":
        acc.professor=professor
    db.session.add(acc)
    db.session.commit()#글수정
    if(attendee==None):
        return
    attend_list=[]
    professor_acc=Attendee.query.filter_by(user_no=user_info["user_no"],lecture_no=no,permission=3).first()
    attend_list.append(professor_acc.attendee_no)
    for attendee_user in attendee:#참석자 수정 시작
        attendee_user=attendee_user.replace("'",'"')
        user=json.loads(attendee_user)
        user_email=user["email"]
        user_name=user["name"]
        user_acc=User.query.filter_by(email=user_email,name=user_name).first()
        if user_acc==None:
            continue
        attend_acc=Attendee.query.filter_by(user_no=user_acc.user_no,lecture_no=no).first()
        if attend_acc==None:
            attend=Attendee(user_no=user_acc.user_no,lecture_no=no,permission=user_acc.permission)
            db.session.add(attend)
            db.session.commit
            this_attendee=Attendee.query.order_by(Attendee.attendee_no.desc()).first()
            attend_list.append(this_attendee.attendee_no)
        else:
            attend_list.append(attend_acc.attendee_no)
    attend=Attendee.query.filter_by(lecture_no=no).all()#기존에서 사라진사람 삭제
    for att in attend:
        if att.attendee_no not in attend_list:
            db.session.delete(att)
            db.session.commit


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

def major_listing(major):
    acc=Lecture.query.filter_by(major=major).all()
    major_list_result=[]
    for lecture in acc:
        tmp={}
        tmp["lecture_no"]=vars(lecture)["lecture_no"]
        tmp["lecture_name"]=vars(lecture)["lecture_name"]
        tmp["year"]=vars(lecture)["year"]
        tmp["semester"]=vars(lecture)["semester"]
        tmp["major"]=vars(lecture)["major"]   
        tmp["separated"]=vars(lecture)["separated"]
        tmp["professor"]=vars(lecture)["professor"]    
        major_list_result.append(tmp)
    return major_list_result

def attendee_add(user_no,lecture_no,perm):
    acc=Attendee(user_no=user_no,lecture_no=lecture_no,permission=perm)
    db.session.add(acc)
    db.session.commit

def attendee_listing(lecture_no):
    acc=Attendee.query.filter_by(lecture_no=lecture_no)
    attendee_user=[]
    attendee_list_result=[]
    for attendee in acc:
        attendee_user.append(attendee.user_no)
    for user_no in attendee_user:
        acc=User.query.filter_by(user_no=user_no).first()
        if acc.permission !=1:#학생만뽑음
            continue
        tmp={}
        tmp["user_no"]=acc.user_no
        tmp["email"]=acc.email
        tmp["name"]=acc.name
        tmp["major"]=acc.major
        tmp["permission"]=acc.permission 
        attendee_list_result.append(tmp)
    return attendee_list_result

def lecture_access_check(user_no,lecture_no):
    acc=Attendee.query.filter_by(lecture_no=lecture_no,user_no=user_no,permission=3).first()
    if(acc==None):
        return 0
    return 1

def mod_lecutre_listing(lecture_no):
    lecture_list_result={}
    acc=Lecture.query.filter_by(lecture_no=lecture_no).first()
    lecture_list_result["lecture_no"]=vars(acc)["lecture_no"]
    lecture_list_result["lecture_name"]=vars(acc)["lecture_name"]
    lecture_list_result["year"]=vars(acc)["year"]
    lecture_list_result["semester"]=vars(acc)["semester"]
    lecture_list_result["major"]=vars(acc)["major"]
    lecture_list_result["separated"]=vars(acc)["separated"]
    lecture_list_result["professor"]=vars(acc)["professor"]

    attend_list_result=[]
    attend_list=Attendee.query.filter_by(lecture_no=lecture_no).all()
    for att in attend_list:
        if att.permission==3 or att.permission==0:
            continue
        tmp={}
        acc=User.query.filter_by(user_no=att.user_no).first()
        tmp["email"]=vars(acc)["email"]
        tmp["name"]=vars(acc)["name"]
        tmp["major"]=vars(acc)["major"]
        attend_list_result.append(tmp)

    return lecture_list_result,attend_list_result