from celery import Celery, Task
from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize
from sqlalchemy import create_engine, orm
from sqlalchemy import Column, Text, Integer, String, Boolean, ForeignKey,Float
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.dialects.mysql import LONGTEXT

from kr_stt_work import (
    KorStt
)
from jp_stt_work import JpStt
from original_text import Original_stt

import os
import uuid
import requests
import time
import re
import nltk
import json

nltk.download('punkt')

env = os.environ
base = declarative_base()

BROKER = os.environ['REDIS_BACKEND']
CELERY_RESULT_BACKEND = os.environ['REDIS_BACKEND']
celery = Celery("tasks", broker=BROKER, backend=CELERY_RESULT_BACKEND)

def get_session():
    engine = create_engine(f"mysql+pymysql://{env['SQL_USER']}:{env['SQL_PASSWORD']}@{env['SQL_HOST']}:{env['SQL_PORT']}/{env['SQL_DATABASE']}", pool_pre_ping=True)
    base.metadata.bind = engine
    return orm.scoped_session(orm.sessionmaker())(bind=engine)

class Stt(base):
    __tablename__ = "STT"
    stt_no = Column(Integer, primary_key=True)
    user_no = Column(Integer, ForeignKey("USER.user_no"), nullable=False)
    assignment_no = Column(Integer, ForeignKey("ASSIGNMENT.assignment_no"), nullable=False)
    wav_file = Column(String(36), nullable=False)

class SttJob(base):
    __tablename__ = "STTJOB"
    job_id = Column(String(36), primary_key=True)
    stt_no = Column(Integer, ForeignKey("STT.stt_no"), nullable=False)
    sound = Column(Text, nullable=False)
    startidx = Column(Text, nullable=False)
    endidx = Column(Text, nullable=False)
    silenceidx = Column(Text, nullable=False)
    stt_result = Column(LONGTEXT, nullable=True)
    is_seq = Column(Boolean, default=False, nullable=False)
    stt_seq = Column(Integer, default=0,nullable=True)
    delay = Column(Float, nullable=True, default=0.0)

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

class DBTask(Task):
    _session: Session = None

    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     if self._session is not None:
    #         self._session.close()
    #         self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = get_session()
        return self._session

@celery.task(base=DBTask, bind=True)
def do_stt_work(self, filename, locale="ko", stt_seq=0):
    result_stt_json = None
    session = self.session
    self.update_state(state='INDEXING')
    if(locale=="jp"):
        stt=JpStt()
    else:
        stt=KorStt()
    self.update_state(state='STT')

    try:
        delay=get_delay(filename)
        result_stt_json=stt.execute(filename)
    except Exception as e:
        print(e)
        self.update_state(state=e.args[0])
        session.rollback()

    stt_db = session.query(Stt).filter_by(wav_file=filename).first()
    if not stt_db:
        session.rollback()
        return False

    print("request id = ",self.request.id, "stt_no = ", stt_db.stt_no)
    job = SttJob(
        job_id=self.request.id,
        stt_no=stt_db.stt_no,
        sound="",
        startidx="",
        endidx="",
        silenceidx="",
        stt_seq=stt_seq,
        delay=delay,
    )
    job.stt_result = result_stt_json if result_stt_json != None else "STT error"
    session.add(job)
    session.commit()
    session.close()
    return result_stt_json

@celery.task(base=DBTask, bind=True)
def do_original_text_stt_work(self, filename, locale="ko",stt_no=None,stt_seq=0):
    result_stt_json = None
    session = self.session
    self.update_state(state='INDEXING')
    stt=Original_stt()
    self.update_state(state='STT')
    print("filename = ", filename)
    try:
        delay=get_delay(filename)
        result_stt_json=stt.execute(filename)
    except Exception as e:
        print(e)
        self.update_state(state=e.args[0])
    print("result_stt_json = ", result_stt_json)
    print("1stt_no = ", stt_no)
    if not stt_no:
        stt_db = session.query(Stt).filter_by(wav_file=filename).first()
        if not stt_db:
            print("not stt_db")
            session.rollback()
            session.update_state(state="STT DB error")
            return False
        stt_no=stt_db.stt_no

    print("request id = ",self.request.id, "stt_no = ", stt_no)
    job = SttJob(
        job_id=self.request.id,
        stt_no=stt_no,
        sound="",
        startidx="",
        endidx="",
        silenceidx="",
        stt_seq=stt_seq,
        delay=delay,
    )
    job.stt_result = "Origin text error" if result_stt_json == None else result_stt_json
    session.add(job)
    session.commit()
    session.close()
    return result_stt_json


def get_delay(audio_file):
    filepath = f"{os.environ['UPLOAD_PATH']}/{audio_file}.mp3"
    myaudio = AudioSegment.from_file(filepath)
    dBFS = myaudio.dBFS
    nonsilent_ranges = silence.detect_nonsilent(myaudio, min_silence_len=1000, silence_thresh=dBFS-16,seek_step=100)
    if nonsilent_ranges:
        start_time = nonsilent_ranges[0][0] / 1000  # 밀리초를 초로 변환
        return start_time
    else:
        return 0