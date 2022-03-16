from server import db
import os
import sys
import hashlib
import base64

class User(db.Model):
    __tablename__ = "user"

    user_no = db.Column(db.Integer,primary_key=True)
    id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=True, nullable=False)
    permission = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    login_fail_limit = db.Column(db.Integer, default=0)
    project_no = db.Column(db.Integer, db.ForeignKey("project.project_no"), nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.password = self.encrypt_password(self.password)
    
    # 송신 패스워드 암호화
    def encrypt_password(self, password):#db에서 비밀번호부분 뽑아오고 salt값을 추출하여 암호화
        salt = os.urandom(32)
        encrypt_passwd = base64.b64encode(salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=128))
        return encrypt_passwd
    
    # 패스워드 해시 값 체크
    #def verify_password(self, password): # db자체에 해쉬값이 박히므로 암호화된 입력값이랑 비교해주면 될듯함
    #    return self.password
    
class Project(db.Model):
    __tablename__ = "project"
    project_no = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime,nullable=False)
    end_date = db.Column(db.DateTime,nullable=False)

class Script(db.Model):
    __tablename__ = "script"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)
    project_no = db.Column(db.Integer, db.ForeignKey("project.project_no"), nullable=False)
    script_name = db.Column(db.String(50), unique=True, nullable=False)

class Analysis(db.Model):
    __tablename__ = "analysis"
    
    xml_no = db.Column(db.Integer, primary_key=True)
    upload_time = db.Column(db.DateTime, nullable=False)
    project_no = db.Column(db.Integer, db.ForeignKey("project.project_no"), nullable=False)
    user_no = db.Column(db.Integer, db.ForeignKey("user.user_no"), nullable=False)
    path = db.Column(db.String(100), nullable=False, unique=True)
    comment = db.Column(db.String(1000), nullable=True)
    




