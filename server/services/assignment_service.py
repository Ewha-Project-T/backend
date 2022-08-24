from distutils.command.upload import upload

from server.apis import assignment
from ..model import Attendee, User, Lecture, Assignment,Prob_region
from server import db
from functools import wraps
from flask_jwt_extended import create_refresh_token, create_access_token, verify_jwt_in_request, get_jwt, get_jwt_identity
import json
import os

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

def make_as(lecture_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region=""):
    acc=Assignment(lecture_no=lecture_no,week=week,limit_time=limit_time,as_name=as_name,as_type=as_type,keyword=keyword,description=description,re_limit=re_limit,speed=speed,disclosure=disclosure,original_text=original_text,upload_url=upload_url)
    db.session.add(acc)
    db.session.commit
    this_assignment=Assignment.query.order_by(Assignment.assignment_no.desc()).first()
    for reg in region:
        reg=reg.replace("'",'"')
        json_reg=json.loads(reg)
        reg_index=json_reg["index"]
        reg_start=json_reg["start"]
        reg_end=json_reg["end"]
        pr=Prob_region(assignment_no=this_assignment.assignment_no,region_index=reg_index,start=reg_start,end=reg_end)
        db.session.add(pr)
        db.session.commit


def mod_as(lecture_no,as_no,week,limit_time,as_name,as_type,keyword,description,re_limit,speed,disclosure,original_text="",upload_url="",region=""):
    acc=Assignment.query.filter_by(assignment_no=as_no).first()
    if(lecture_no!=""):
        acc.lecture_no=lecture_no
    if(week!=""):
        acc.week=week
    if(limit_time!=""):
        acc.limit_time=limit_time
    if(as_name!=""):
        acc.as_name=as_name
    if(as_type!=""):
        acc.as_type=as_type
    if(keyword!=""):
        acc.keyword=keyword
    if(description!=""):
        acc.description=description
    if(re_limit!=""):
        acc.relimit=re_limit
    if(speed!=""):
        acc.speed=speed
    if(disclosure!=""):
        acc.disclosure=disclosure
    if(original_text!=""):
        acc.original_text=original_text
    if(upload_url!=""):
        acc.upload_url=upload_url
    db.session.add(acc)
    db.session.commit
    Prob_region.query.filter_by(assignment_no=as_no).delete()
    db.session.commit

    for reg in region:
        reg=reg.replace("'",'"')
        json_reg=json.loads(reg)
        reg_index=json_reg["index"]
        reg_start=json_reg["start"]
        reg_end=json_reg["end"]
        pr=Prob_region(assignment_no=as_no,region_index=reg_index,start=reg_start,end=reg_end)
        db.session.add(pr)
        db.session.commit


def get_wav_url(as_no):
    acc=Assignment.query.filter_by(assignment_no=as_no).first()
    return acc.upload_url

def delete_assignment(assignment_no):
    acc = Assignment.query.filter_by(assignment_no=assignment_no).first()
    db.session.delete(acc)
    db.session.commit
