from celery import Celery, Task
from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize
from sqlalchemy import create_engine, orm
from sqlalchemy import Column, Text, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

from kr_stt_work import (
    KorStt
)
from jp_stt_work import JpStt

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
    stt_result = Column(Text, nullable=True)
    is_seq = Column(Boolean, default=False, nullable=False)

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
def do_stt_work(self, filename, locale="ko-KR"):
    session = self.session
    self.update_state(state='INDEXING')
    if(locale=="ja-JP"):
        length,sound,startidx,endidx,silenceidx,myaudio=JpStt.basic_indexing(filename)
    else:
        length,sound,startidx,endidx,silenceidx,myaudio=KorStt.basic_indexing(filename)
    self.update_state(state='STT')
    domain = os.getenv("DOMAIN", "https://edu-trans.ewha.ac.kr:8443")

    files = []
    local_file = []
    if(locale=="ja-JP"):
        for i in range(length):
            filetmp = uuid.uuid4()
            filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
            myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
            files += [ domain + "/" + filepath ]
            local_file += [ filepath ]
    else:
        for i in range(len(sound)):
            filetmp = uuid.uuid4()
            filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
            myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
            files += [ domain + "/" + filepath ]
            local_file += [ filepath ]
    res=[0 for i in range(len(local_file))]

    try:
        result = {'textFile': '', 'timestamps': [], 'annotations': []}
        if not len(files) > 0:  
            raise Exception("INVALID-FILE")
        
        if(locale=="ja-JP"):
            for i in range(len(local_file)):
                response=JpStt.req_upload(file=local_file[i], completion='sync')
                if response.status_code != 200:
                    # raise RuntimeError("API server does not response correctly")
                    try:
                        response.raise_for_status()
                        text = response.text.strip()
                        if len(text) > 0:
                            print("Recognized text: ", text)
                        else:
                            print("No speech detected")
                    except requests.exceptions.HTTPError as e:
                        print("HTTP error: ", e)
                    except requests.exceptions.ConnectionError as e:
                        print("Error connecting to server: ", e)
                    except requests.exceptions.Timeout as e:
                        print("Timeout error: ", e)
                    except requests.exceptions.RequestException as e:
                        print("Error: ", e)
                res[i] = json.loads(response.text)
        else:
            webhook_res = requests.post(
                os.environ["STT_URL"],
                headers={
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": os.environ["STT_KEY"]
                },
                json={
                    "contentUrls": files,
                    "properties": {
                        "diarizationEnabled": False,
                        "wordLevelTimestampsEnabled": True,
                        "punctuationMode": "DictatedAndAutomatic",
                        "profanityFilterMode": "Masked"
                    },
                    "locale": locale,
                    "displayName": "Transcription of file using default model for en-US"
                }
            ).json()
            url = webhook_res["links"]["files"]
            res = { 'values': [] }
            while len(res["values"]) == 0:
                res = requests.get(
                    url,
                    headers={ "Ocp-Apim-Subscription-Key": os.environ['STT_KEY'] }
                ).json()

                time.sleep(1)
            for file in local_file:
                os.unlink(file)

        self.update_state(state='STT-DONE')

        for i in range(len(sound)):
            result['timestamps'].append({'start': startidx[i], 'end': endidx[i]})
    except IndexError as e: # for none recognized text exception (recog["recognizedPhrases"][0]["nBest"][0]["lexical"])
        print(e)
        self.update_state(state='INDEX_ERROR')
    except Exception as e:
        print(e)
        self.update_state(state=e.args[0])
    if(locale=="ja-JP"):
        jstt = JpStt() 
        print(res)
        stt, pause_result, delay_result, pause_idx, start_idx, end_idx=jstt.basic_do_stt(length,res,sound,startidx,endidx,silenceidx)
    else:
        kstt = KorStt() 
        stt, pause_result, delay_result, pause_idx = kstt.basic_do_stt(res, sound, silenceidx) #인자맞추기 필요
    if(locale=="ja-JP"):
        result=JpStt.basic_annotation_stt(result,stt,pause_idx)
    else:
        result=KorStt.basic_annotation_stt(result,stt,pause_idx)    
    
    stt = session.query(Stt).filter_by(wav_file=filename).first()
    if not stt:
        return False

    job = SttJob(
        job_id=self.request.id,
        stt_no=stt.stt_no,
        sound=repr(sound),
        startidx=repr(startidx),
        endidx=repr(endidx),
        silenceidx=repr(silenceidx),
    )

    job.stt_result = repr(result)
    session.add(job)
    session.commit()
    return result

@celery.task(base=DBTask, bind=True)
def do_sequential_stt_work(self, filename, index, locale="ko-KR"):
    return 0
