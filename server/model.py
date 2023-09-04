from ast import keyword
from calendar import week
from tracemalloc import start
from server import db
import os
import sys
import hashlib
import base64
from datetime import datetime,timedelta

class User(db.Model):
    __tablename__ = "USER"

    user_no = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(50), nullable=False)
    permission = db.Column(db.Integer, default=1)
    login_fail_limit = db.Column(db.Integer, default=0)
    access_check = db.Column(db.Integer, default=0)
    access_check_admin = db.Column(db.Integer, default=0)
    access_code= db.Column(db.String(150),nullable=True)
    access_code_time=db.Column(db.DateTime, onupdate=datetime.utcnow()+timedelta(hours=9))#테이블 삭제시 오류날수도

    assignment= db.relationship("Assignment",back_populates="user",cascade="all, delete",passive_deletes=True,)
    attendee= db.relationship("Attendee",back_populates="user",cascade="all, delete",passive_deletes=True,)
    stt= db.relationship("Stt",back_populates="user",cascade="all, delete",passive_deletes=True,)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.password = self.encrypt_password(self.password) #DB생성시 pw 자동 암호화
    
    # 송신 패스워드 암호화
    def encrypt_password(self,password):#db에서 비밀번호부분 뽑아오고 salt값을 추출하여 암호화
        salt = os.urandom(32)
        encrypt_passwd = base64.b64encode(salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=128))
        return encrypt_passwd


class Lecture(db.Model):
    __tablename__ = "LECTURE"
    lecture_no = db.Column(db.Integer, primary_key=True)
    lecture_name = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(7), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    major = db.Column(db.String(50), nullable=False)
    separated = db.Column(db.String(5), nullable=False)
    professor = db.Column(db.String(50), nullable=False)

    attendee= db.relationship("Attendee",back_populates="lecture",cascade="all, delete",passive_deletes=True,)
    assignment= db.relationship("Assignment",back_populates="lecture",cascade="all, delete",passive_deletes=True,)
class Attendee(db.Model):
    __tablename__="ATTENDEE"
    attendee_no = db.Column(db.Integer, primary_key=True)
    user_no = db.Column(db.Integer, db.ForeignKey("USER.user_no", ondelete="CASCADE"), nullable=True)
    lecture_no = db.Column(db.Integer, db.ForeignKey("LECTURE.lecture_no",ondelete="CASCADE"), nullable=True)
    permission = db.Column(db.Integer, default=1)

    user = db.relationship("User", back_populates="attendee")
    lecture = db.relationship("Lecture",back_populates="attendee")

    assignment_check= db.relationship("Assignment_check",back_populates="attendee",cascade="all, delete",passive_deletes=True,)
class Assignment(db.Model):
    __tablename__="ASSIGNMENT"
    assignment_no = db.Column(db.Integer, primary_key=True)
    user_no = db.Column(db.Integer, db.ForeignKey("USER.user_no", ondelete="CASCADE"), nullable=True)
    lecture_no = db.Column(db.Integer, db.ForeignKey("LECTURE.lecture_no", ondelete="CASCADE"), nullable=True)
    week = db.Column(db.String(20), nullable=False)
    limit_time = db.Column(db.DateTime, nullable=False)
    as_name = db.Column(db.String(50), nullable=False)
    as_type = db.Column(db.String(10), nullable=False)
    keyword = db.Column(db.Text)
    translang= db.Column(db.String(20))
    description = db.Column(db.Text)
    re_limit = db.Column(db.String(10))
    speed = db.Column(db.Float)
    disclosure= db.Column(db.Integer,default=0)
    original_text= db.Column(db.Text)
    upload_url= db.Column(db.String(100))
    dest_translang= db.Column(db.String(20))
    assign_count= db.Column(db.Integer, default=1)
    keyword_open= db.Column(db.Boolean, default=0)
    
    user = db.relationship("User",back_populates="assignment")
    lecture = db.relationship("Lecture",back_populates="assignment")

    assignment_check= db.relationship("Assignment_check",back_populates="assignment",cascade="all, delete",passive_deletes=True,)
    stt= db.relationship("Stt",back_populates="assignment",cascade="all, delete",passive_deletes=True,)
    prob_region=db.relationship("Prob_region",back_populates="assignment",cascade="all, delete",passive_deletes=True,)

class Assignment_check(db.Model):
    __tablename__="ASSIGNMENT_CHECK"
    check_no = db.Column(db.Integer, primary_key=True)
    assignment_no = db.Column(db.Integer, db.ForeignKey("ASSIGNMENT.assignment_no", ondelete="CASCADE"), nullable=True)
    attendee_no = db.Column(db.Integer, db.ForeignKey("ATTENDEE.attendee_no", ondelete="CASCADE"), nullable=True)
    assignment_check = db.Column(db.Integer, default=0)
    professor_review= db.Column(db.Text)
    user_trans_result= db.Column(db.Text) # 추후 삭제 예정
    ae_text = db.Column(db.Text)
    ae_denotations = db.Column(db.Text)
    ae_attributes = db.Column(db.Text)
    submit_time=db.Column(db.DateTime, onupdate=datetime.utcnow()+timedelta(hours=9))#테이블 삭제시 오류날수도
    submit_cnt = db.Column(db.Integer, default=0)
    end_submission = db.Column(db.Boolean, default = False)
   
    attendee = db.relationship("Attendee", back_populates="assignment_check")
    assignment = db.relationship("Assignment", back_populates="assignment_check")

    feedback= db.relationship("Assignment_feedback",back_populates="check",cascade="all, delete",passive_deletes=True,)
    check_list= db.relationship("Assignment_check_list", back_populates="check", cascade="all, delete", passive_deletes=True,)
class Assignment_feedback(db.Model):
    __tablename__="ASSIGNMENT_FEEDBACK"
    feedback_no= db.Column(db.Integer, primary_key=True)
    check_no = db.Column(db.Integer, db.ForeignKey("ASSIGNMENT_CHECK.check_no", ondelete="CASCADE"))
    target_text = db.Column(db.Text, nullable=False)
    text_type = db.Column(db.Text)
    comment = db.Column(db.Text, nullable=False)
    start= db.Column(db.Integer)
    end= db.Column(db.Integer)
    part= db.Column(db.Integer)

    check = db.relationship("Assignment_check", back_populates="feedback")

class Assignment_check_list(db.Model):
    __tablename__="ASSIGNMENT_CHECK_LIST"
    acl_no=db.Column(db.Integer, primary_key=True)
    check_no = db.Column(db.Integer, db.ForeignKey("ASSIGNMENT_CHECK.check_no", ondelete="CASCADE"), nullable=True)
    acl_uuid= db.Column(db.String(36), nullable=False)

    check = db.relationship("Assignment_check", back_populates="check_list")
class Stt(db.Model):
    __tablename__ = "STT"
    stt_no = db.Column(db.Integer, primary_key=True)
    user_no = db.Column(db.Integer, db.ForeignKey("USER.user_no", ondelete="CASCADE"), nullable=False)
    assignment_no = db.Column(db.Integer, db.ForeignKey("ASSIGNMENT.assignment_no", ondelete="CASCADE"), nullable=False)
    wav_file = db.Column(db.String(36), nullable=False)

    user=db.relationship("User", back_populates="stt")
    assignment = db.relationship("Assignment", back_populates="stt")

    sttjob= db.relationship("SttJob",back_populates="stt",cascade="all, delete",passive_deletes=True,)
class Prob_region(db.Model):
    __tablename__="PROB_REGION"
    region_no= db.Column(db.Integer, primary_key=True)
    assignment_no = db.Column(db.Integer, db.ForeignKey("ASSIGNMENT.assignment_no", ondelete="CASCADE"), nullable=False)
    region_index = db.Column(db.String(10))
    start = db.Column(db.String(10))
    end = db.Column(db.String(10))
    upload_url = db.Column(db.Text, nullable=False)
    job_id = db.Column(db.String(36), nullable=False)

    assignment = db.relationship("Assignment", back_populates="prob_region")

class SttJob(db.Model):
    __tablename__ = "STTJOB"
    job_id = db.Column(db.String(36), primary_key=True)
    stt_no = db.Column(db.Integer, db.ForeignKey("STT.stt_no", ondelete="CASCADE"),nullable=False)
    sound = db.Column(db.Text, nullable=False)
    startidx = db.Column(db.Text, nullable=False)
    endidx = db.Column(db.Text, nullable=False)
    silenceidx = db.Column(db.Text, nullable=False)
    stt_result = db.Column(db.Text, nullable=True)
    is_seq = db.Column(db.Boolean, default=False, nullable=False)

    stt = db.relationship("Stt", back_populates="sttjob")

class Feedback2(db.Model):
    __tablename__="FEEDBACK"
    feed_no = db.Column(db.Integer, primary_key=True)
    attendee_no = db.Column(db.Integer, db.ForeignKey("ATTENDEE.attendee_no", ondelete="CASCADE"), nullable=True)
    check_no= db.Column(db.Integer, db.ForeignKey("ASSIGNMENT_CHECK.check_no", ondelete="CASCADE"), nullable=True)
    submission_count = db.Column(db.Integer, default=0)
    translation_error = db.Column(db.Integer, default=0)
    omission = db.Column(db.Integer, default=0)
    expression = db.Column(db.Integer, default=0)
    intonation = db.Column(db.Integer, default=0)
    grammar_error = db.Column(db.Integer, default=0)
    silence = db.Column(db.Integer, default=0)
    filler = db.Column(db.Integer, default=0)
    backtracking = db.Column(db.Integer, default=0)
    others = db.Column(db.Integer, default=0)

class Feedback(db.Model):
    __tablename__="feedbackww"
    idx = db.Column(db.Integer, primary_key = True)
    attendee_no = db.Column(db.Integer, db.ForeignKey("ATTENDEE.attendee_no", ondelete="CASCADE"), nullable=True)
    check_no= db.Column(db.Integer, db.ForeignKey("ASSIGNMENT_CHECK.check_no", ondelete="CASCADE"), nullable=True)
    