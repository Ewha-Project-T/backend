from celery import Celery, Task
from pydub import AudioSegment, silence
from nltk.tokenize import sent_tokenize
from sqlalchemy import create_engine, orm
from sqlalchemy import Column, Text, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

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

def process_stt_result(stt):
    result = stt
    result = re.sub('니다', '니다. ', result)
    result = re.sub('까요', '까요. ', result)
    result = result.split()
    for i in range(len(result)):
        if result[i] == '음' or result[i] == '그' or result[i] == '어':
            result[i] = result[i] + "(filler)"
        if len(result) > 1 and result[i-1][0] == result[i][0] and result[i-1] in result[i]:
            result[i] = result[i] + "(backtracking)"
        elif len(result) > 1 and result[i-1][0] == result[i][0] and len(result[i-1]) <= len(result[i]):
            result[i] = result[i] + "(backtracking)"

    result = ' '.join(result)
    return result

def basic_indexing(filename):
    filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.wav"
    myaudio = AudioSegment.from_file(filepath)
    dBFS = myaudio.dBFS
    sound = silence.detect_nonsilent(
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16, seek_step=100)  # 1초 이상의 silence
    sound = [[(start), (stop)] for start, stop in sound]
    startidx = []
    endidx = []
    silenceidx = []
    for i in range(0, len(sound)):
        startidx.append(sound[i][0])
        endidx.append(sound[i][1] + 200)
        if i < len(sound) - 1:
            silenceidx.append(sound[i + 1][0] - sound[i][1])
    return sound, startidx, endidx, silenceidx, myaudio

def basic_do_stt(res,sound,silenceidx):
    flag = True
    text = ''
    delay_result = 0
    pause_result = 0
    pause_idx=[]
    values = res["values"]
    tmp_textFile= ['' for i in range(len(values))]
    for i in range(len(values)):
        tmp_seq=values[i]["name"]
        tmp_seq = re.findall("-?\d+", tmp_seq)
        if not tmp_seq:#report.json 처리
            continue
        tmp_seq=int(tmp_seq[0])
        kind = values[i]["kind"]
        if kind != "Transcription":
            continue

        recog = requests.get(values[i]["links"]["contentUrl"]).json()
        if(not recog["combinedRecognizedPhrases"]):
            continue
        stt = process_stt_result(recog["combinedRecognizedPhrases"][0]["lexical"])
        text = stt
        sentences = sent_tokenize(stt)
        for sentence in sentences:
            if sentence.endswith('.'):
                flag = True
            else:
                flag = False
        if i < len(sound) - 1:
            if flag == False:
                print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                text = text+'\n'
                pause_idx.append(silenceidx[i])
            else:
                # 통역 개시 지연구간
                print("(delay: " + str(silenceidx[i]) + "sec)")
                text = text+'\n'
                delay_result += silenceidx[i]
        tmp_textFile[tmp_seq] = text

    tmp_text=''.join(tmp_textFile)                
    return tmp_text, pause_result, delay_result, pause_idx

def basic_annotation_stt(result,stt,pause_idx):
    p = re.compile('(\w\(filler\)|\w+\s\w+\(backtracking\))')
    fidx = []
    while (True):
        f = p.search(stt)
        if f == None:
            break
        fidx.append([f.start(), f.end()])
        stt = re.sub("(\(filler\)|\(backtracking\))", "", stt, 1)

    for i in range(len(fidx)):
        if stt[fidx[i][0]] == '음' or stt[fidx[i][0]] == '그' or stt[fidx[i][0]] == '어':
            result['annotations'].append({'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
        else:
            result['annotations'].append({'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

    pidx = [m.start(0) + 1 for m in re.finditer('[^\.^\n]\n', stt)]
    for i in range(len(pidx)):  # pause, delay 구분 없이 pause 로 통일
        result['annotations'].append({'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': pause_idx[i]})

    if stt.endswith("\n"):
        stt = stt[:-1]
    result['textFile']=stt   
    return result

@celery.task(base=DBTask, bind=True)
def do_stt_work(self, filename, locale="ko-KR"):
    session = self.session
    self.update_state(state='INDEXING')
    
    sound,startidx,endidx,silenceidx,myaudio=basic_indexing(filename)
    self.update_state(state='STT')
    
    domain = os.getenv("DOMAIN", "https://translation-platform.site:8443")

    files = []
    local_file = []
    for i in range(len(sound)):
        filetmp = uuid.uuid4()
        filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
        myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
        files += [ domain + "/" + filepath ]
        local_file += [ filepath ]

    try:
        result = {'textFile': '', 'timestamps': [], 'annotations': []}
        if not len(files) > 0:
            raise Exception("INVALID-FILE")
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

    stt,pause_result, delay_result, pause_idx=basic_do_stt(res,sound,silenceidx)
    result=basic_annotation_stt(result,stt,pause_idx)    
    
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
