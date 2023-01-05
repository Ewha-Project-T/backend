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
            self._session, self._engine = get_session()
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

@celery.task(base=DBTask, bind=True)
def do_stt_work(self, filename, locale="ko-KR"):
    session = self.session

    self.update_state(state='INDEXING')

    filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.wav"
    myaudio = AudioSegment.from_file(filepath)
    dBFS = myaudio.dBFS
    sound = silence.detect_nonsilent(
        myaudio, min_silence_len=1000, silence_thresh=dBFS - 16)  # 1초 이상의 silence
    sound = [[(start), (stop)] for start, stop in sound]
    startidx = []
    endidx = []
    silenceidx = []
    for i in range(0, len(sound)):
        startidx.append(sound[i][0])
        endidx.append(sound[i][1] + 200)
        if i < len(sound) - 1:
            silenceidx.append(sound[i + 1][0] - sound[i][1])

    self.update_state(state='STT')
    
    domain = os.getenv("DOMAIN", "https://ewha.ltra.cc")

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
        flag = True
        text = ''
        delay_result = 0
        pause_result = 0

        values = res["values"]
        for i in range(len(values)):
            kind = values[i]["kind"]
            if kind != "Transcription":
                continue

            recog = requests.get(values[i]["links"]["contentUrl"]).json()
            if(not recog["recognizedPhrases"]):
                continue
            stt = process_stt_result(recog["recognizedPhrases"][0]["nBest"][0]["lexical"])
            text += stt
            sentences = sent_tokenize(stt)
            for sentence in sentences:
                # print(sentence)
                if sentence.endswith('.'):
                    flag = True
                else:
                    flag = False
            if i < len(sound) - 1:
                if flag == False:
                    print("(pause: " + str(silenceidx[i])+"sec)")  # 침묵
                    text = text+'\n'
                    pause_result += silenceidx[i]
                else:
                    # 통역 개시 지연구간
                    print("(delay: " + str(silenceidx[i]) + "sec)")
                    text = text+'\n'
                    delay_result += silenceidx[i]

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
                    result['annotations'].append(
                        {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
                else:
                    result['annotations'].append(
                        {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

            pidx = []
            indx = -1
            while True:
                indx = stt.find('\n', indx + 1)
                if indx == -1:
                    break
                pidx.append(indx)
            for i in range(len(pidx)): # pause, delay 구분 없이 pause 로 통일
                result['annotations'].append({'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': silenceidx[i]})

            result['textFile'] += stt
    except IndexError as e: # for none recognized text exception (recog["recognizedPhrases"][0]["nBest"][0]["lexical"])
        print(e)
        # session.rollback()
        self.update_state(state='INDEX_ERROR')
    except Exception as e:
        # session.rollback()
        self.update_state(state=e.args[0])

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
    session = get_session()

    filepath = f"{os.environ['UPLOAD_PATH']}/{filename}.wav"
    myaudio = AudioSegment.from_file(filepath)

    sounds = []
    silenceidxs = []
    startidxs= []
    endidxs = []
    temp = []
    for i in range(len(index)):
        audio_part = myaudio[index[i][0]:index[i][1]]
        # audio_part.export(f"{os.environ['UPLOAD_PATH']}/{}")
        dBFS = myaudio.dBFS
        sound = silence.detect_nonsilent(audio_part, min_silence_len=1000, silence_thresh=dBFS - 16)
        sound = [[(start), (stop)] for start, stop in sound]
        startidx = []
        endidx = []
        silenceidx = []
        for i in range(0, len(sound)):
            startidx.append(sound[i][0])
            endidx.append(sound[i][1] + 200)
            if i < len(sound) - 1:
                silenceidx.append(sound[i + 1][0] - sound[i][1])
        sounds += [ sound ]
        startidxs += [ startidx ]
        endidxs += [ endidx ]
        silenceidxs += [ silenceidx ]

        self.update_state(state='STT')
    
        domain = os.getenv("DOMAIN", "https://ewha.ltra.cc")

        files = []
        local_file = []
        for i in range(len(sound)):
            filetmp = uuid.uuid4()
            filepath = f"{os.environ['UPLOAD_PATH']}/{filetmp}.wav"
            myaudio[startidx[i]:endidx[i]].export(filepath, format="wav")
            files += [ domain + "/" + filepath ]
            local_file += [ filepath ]
        
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

        temp += [ res ]

    result = {'textFile': '', 'timestamps': [], 'annotations': []}
    for i in range(len(sounds)):
        for k in range(len(sounds[i])):
            result['timestamps'].append({'start': index[i][k] + startidxs[i][k], 'end': index[i][k] + endidxs[i][k]})

        text = ''
        res = temp[i]
        values = res["values"]
        for k in range(len(values)):
            kind = values[i]["kind"]
            if kind != "Transcription":
                continue

            recog = requests.get(values[i]["links"]["contentUrl"]).json()
            stt = process_stt_result(recog["recognizedPhrases"][0]["nBest"][0]["lexical"])
            text += stt
            sentences = sent_tokenize(stt)
            for sentence in sentences:
                # print(sentence)
                if sentence.endswith('.'):
                    flag = True
                else:
                    flag = False
            if i < len(sounds[i]) - 1:
                if flag == False:
                    print("(pause: " + str(silenceidxs[i][k])+"sec)")  # 침묵
                    text = text+'\n'
                    pause_result += silenceidxs[i][k]
                else:
                    # 통역 개시 지연구간
                    print("(delay: " + str(silenceidxs[i][k]) + "sec)")
                    text = text+'\n'
                    delay_result += silenceidxs[i][k]

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
                    result['annotations'].append(
                        {'start': fidx[i][0], 'end': fidx[i][0] + 1, 'type': 'FILLER'})
                else:
                    result['annotations'].append(
                        {'start': fidx[i][0], 'end': fidx[i][1] - 14, 'type': 'BACKTRACKING'})

            pidx = []
            indx = -1
            while True:
                indx = stt.find('\n', indx + 1)
                if indx == -1:
                    break
                pidx.append(indx)
            for i in range(len(pidx)): # pause, delay 구분 없이 pause 로 통일
                result['annotations'].append({'start': pidx[i], 'end': pidx[i] + 1, 'type': 'PAUSE', 'duration': silenceidxs[i]})

            result['textFile'] += stt
    
    stt = session.query(Stt).filter_by(wav_file=filename).first()
    if stt is None:
        return False

    job = SttJob(
        job_id=self.request.id,
        stt_no=stt.stt_no,
        sound=repr(sounds),
        startidx=repr(startidxs),
        endidx=repr(endidxs),
        silenceidx=repr(silenceidxs),
        is_seq=True
    )

    job.stt_result = repr(result)
    session.add(job)
    session.commit()

    return result
