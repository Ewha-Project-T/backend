from server import db
import os
import sys
import hashlib
import base64

class User(db.Model):
    __tablename__ = "USER"

    user_no = db.Column(db.Integer,primary_key=True)
    id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=True, nullable=False)
    permission = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    login_fail_limit = db.Column(db.Integer, default=0)
    project_no = db.Column(db.Integer, db.ForeignKey("PROJECT.project_no"), nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.password = self.encrypt_password(self.password) #함수로 그냥 쓸라우
    
    # 송신 패스워드 암호화
    def encrypt_password(self,password):#db에서 비밀번호부분 뽑아오고 salt값을 추출하여 암호화
        salt = os.urandom(32)
        encrypt_passwd = base64.b64encode(salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=128))
        return encrypt_passwd
    
    # 패스워드 해시 값 체크
    #def verify_password(self, password): # db자체에 해쉬값이 박히므로 암호화된 입력값이랑 비교해주면 될듯함
    #    return self.password
    
class Project(db.Model):
    __tablename__ = "PROJECT"
    project_no = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime,nullable=False)
    end_date = db.Column(db.DateTime,nullable=False)

class Script(db.Model):
    __tablename__ = "SCRIPT"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)
    project_no = db.Column(db.Integer, db.ForeignKey("PROJECT.project_no"), nullable=False)
    script_name = db.Column(db.String(50), unique=True, nullable=False)

class Analysis(db.Model):
    __tablename__ = "ANALYSIS"
    
    xml_no = db.Column(db.Integer, primary_key=True)
    upload_time = db.Column(db.DateTime, nullable=False)
    project_no = db.Column(db.Integer, db.ForeignKey("PROJECT.project_no"), nullable=False)
    user_no = db.Column(db.Integer, db.ForeignKey("USER.user_no"), nullable=False)
    path = db.Column(db.String(100), nullable=False, unique=True)
    safe = db.Column(db.Integer, nullable=True)
    vuln = db.Column(db.Integer, nullable=True)
    host_no = db.Column(db.Integer, db.ForeignKey("HOST_INFO.no"), nullable=False)

class HostInfo(db.Model):
    __tablename__ = "HOST_INFO"

    no = db.Column(db.Integer, primary_key=True)
    project_no = db.Column(db.Integer, db.ForeignKey("PROJECT.project_no"), nullable=False)
    host_name = db.Column(db.String(100), nullable=True)
    analysis_count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, nullable=True)
    types = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(50), nullable=False)

class Code(db.Model):
    __tablename__="CODE"
    
    code_no = db.Column(db.Integer,primary_key=True)
    os = db.Column(db.String(20), nullable=True)
    title_code = db.Column(db.String(10), nullable=True)
    kisa_code = db.Column(db.String(10), nullable=True)


class Comment(db.Model):
    __tablename__="COMMENT"
    comment_no = db.Column(db.Integer, primary_key=True)
    xml_no = db.Column(db.Integer, db.ForeignKey("ANALYSIS.xml_no"), nullable=False)
    title_code = db.Column(db.String(10), nullable=False)
    old_vuln = db.Column(db.String(20), nullable=True)
    new_vuln = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    modifier = db.Column(db.String(20), nullable=False)

class PROJECT_SCRIPT(db.Model):
    __tablename__ = "PROJECT_SCRIPTS_TB"
    no = db.Column(db.Integer,primary_key=True)
    project_no = db.Column(db.Integer, db.ForeignKey("PROJECT.project_no"), nullable=False)
    script_name = db.Column(db.String(100), db.ForeignKey("SCRIPT.script_name"), nullable=False)
    type = db.Column(db.String(10))
    script_no = db.Column(db.Integer, db.ForeignKey("SCRIPT.id"), nullable=False)