from curses import flash
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import os
from flask import Flask,render_template,request,url_for
import uuid,hashlib
import binascii
from ..model import User
from server import db
from datetime import datetime, timedelta


def send_mail(send_from, send_to, subject, message, mtype='plain', files=[],
              server="mail.ewha.ac.kr", port=2525, username='', password=''):
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        mtype (str): choose type 'plain' or 'html'
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = ', '.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message, mtype))

    '''
    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment', filename=Path(path).name)
        msg.attach(part)
    '''
    smtp = smtplib.SMTP(server, port)
    s = smtp.login(username, password)
    if s[0] == 235:
        print('[+] sendmail success')
    else:
        print('[-] Error')
        print(s)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()

def signup_email_validate(sender_email,code):
    #id = os.environ['id']
    #pw = os.environ['pw']
    #email = os.environ['email']
    id = 'x.sw' # id
    pw = 'nlp_project1' # pass
    email ='x.sw@ewha.ac.kr'#mail address
    subject = '[인증코드 발송]Ewha Language Translation Platform 인증 코드 안내'
    with  open('./templates/mail_check.html','rt',encoding='UTF-8') as f:
        print(f.read())
        message = f.read().replace('[code]',code)
        message = message.replace('[email]',sender_email)

    send_mail(send_from=email, send_to=[sender_email],
          subject=subject, message=message,
          mtype='html', username=email, password=pw)


def gen_verify_email_code(user_email):
    salt = str(binascii.hexlify(os.urandom(16)))
    r_key = str(uuid.uuid4())
    code = hashlib.sha512(str(r_key + salt).encode('utf-8')).hexdigest()
    acc = User.query.filter_by(email=user_email).first()
    acc.access_code=code
    db.session.add(acc)
    db.session.commit()
    return code

def get_access_code(user_email):
    acc = User.query.filter_by(email=user_email).first()
    print(acc.access_code_time)
    if(acc.access_code_time+timedelta(minutes=15)>datetime.now()):
        return 0
    return acc.access_code

def access_check_success(user_email):
    acc = User.query.filter_by(email=user_email).first()
    acc.access_check=1
    db.session.add(acc)
    db.session.commit()