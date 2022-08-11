from server import db
import os
import sys
import hashlib
import base64

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

class Attendee(db.Model):
    __tablename__="ATTENDEE"
    attendee_no = db.Column(db.Integer, primary_key=True)
    user_no = db.Column(db.Integer, db.ForeignKey("USER.user_no"), nullable=True)
    lecture_no = db.Column(db.Integer, db.ForeignKey("LECTURE.lecture_no"), nullable=True)
    permission = db.Column(db.Integer, default=1)

class Assignment(db.Model):
    __tablename__="ASSIGNMENT"
    assignment_no = db.Column(db.Integer, primary_key=True)
    lecture_no = db.Column(db.Integer, db.ForeignKey("LECTURE.lecture_no"), nullable=True)
    

class Assignment_check(db.Model):
    __tablename__="ASSIGNMENT_CHECK"
    check_no = db.Column(db.Integer, primary_key=True)
    assignment_no = db.Column(db.Integer, db.ForeignKey("ASSIGNMENT.assignment_no"), nullable=True)
    attendee_no = db.Column(db.Integer, db.ForeignKey("ATTENDEE.attendee_no"), nullable=True)
    assignment_check = db.Column(db.Integer, default=0)


class Stt(db.Model):
    __tablename__ = "STT"
    stt_no = db.Column(db.Integer, primary_key=True)
    user_no = db.Column(db.Integer, db.ForeignKey("USER.user_no"), nullable=False)
    assignment_no = db.Column(db.Integer, db.ForeignKey("ASSIGNMENT.assignment_no"), nullable=False)
    wav_file = db.Column(db.String(36), nullable=False)


