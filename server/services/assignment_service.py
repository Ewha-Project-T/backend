from ..model import Attendee, User, Lecture, Assignment
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
import json

def prob_listing(lecture_no):
    as_list=Assignment.query.filter_by(lecture_no=lecture_no).all()
    as_list_result=[]
    for lec in as_list:
        tmp={}
        tmp["assignment_no"]=vars(lec)["assignment_no"]
        tmp["week"]=vars(lec)["week"]
        tmp["limit_time"]=vars(lec)["limit_time"]
        tmp["as_name"]=vars(lec)["as_name"]
        tmp["as_type"]=vars(lec)["as_type"]
        tmp["keyword"]=vars(lec)["keyword"]
        tmp["description"]=vars(lec)["description"]
        tmp["re_limit"]=vars(lec)["re_limit"]
        tmp["speed"]=vars(lec)["speed"]
        tmp["disclosure"]=vars(lec)["disclosure"]
        tmp["original_text"]=vars(lec)["original_text"]
        tmp["upload_url"]=vars(lec)["upload_url"]
        as_list_result.append(tmp)
    return as_list_result

def make_as(lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text,upload_url):
    acc=Assignment(lecture_no=lecture_no,week=week,limit_time=limit_time,as_name=as_name,as_type=as_type,keyword=keyword,description=description,re_limit=re_limit,speed=speed,disclosure=disclosure,original_text=original_text,upload_url=upload_url)
    db.session.add(acc)
    db.session.commit

def mod_as(as_no,lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text,upload_url):
    acc=Assignment.query.filter_by(assignment_no=as_no).first()
    acc.lecture_no=lecture_no
    acc.week=week
    acc.limit_time=limit_time
    acc.as_name=as_name
    acc.as_type=as_type
    acc.keyword=keyword
    acc.description=description
    acc.relimit=re_limit
    acc.speed=speed
    acc.disclosure=disclosure
    acc.original_text=original_text
    acc.upload_url=upload_url
    db.session.add(acc)
    db.session.commit