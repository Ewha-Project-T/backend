from server.apis.mail import Email, Verify_email
from server.model import Lecture
from .login import Login,Join, LoginRefresh, Logout
from .lecture import Attend, Lecture, Lecture_mod, Lecture_mod_del, Student,Major, Lecture_add
from .assignment import Prob, Prob_del, Prob_submit, Prob_feedback,Prob_mod,Prob_add, prob_upload, Prob_submit_list
from .admin import Admin,Admin2
from .stt import Stt, SttJob, SttSeq, SttSeqJob
from .react_login import Login2,Logout2,CheckToken,Join2
from .react_assignment import  Feedback2, React_Prob, React_Prob_del,React_Prob_add,React_Prob_mod,React_Prob_submit_list,React_Prob_submit,Studentgraphlist,Professorgraphlist
from .react_lecture import React_Lecture,React_Lecture_mod_del,React_Student,React_Lecture_add,React_Lecture_mod



def load_api(api_module):
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(Login2,'/api/user/login',endpoint='login2') # GET POST PUT PATCH DELETE
    api_module.add_resource(Logout2,'/api/user/logout',endpoint='logout2') # GET POST PUT PATCH DELETE
    api_module.add_resource(Join2,'/api/user/join',endpoint='join2') # GET POST PUT PATCH DELETE
    api_module.add_resource(CheckToken,'/api/user/auth',endpoint='checkToken') 
    api_module.add_resource(React_Lecture,'/api/lecture/list',endpoint='react_lecture_list')
    api_module.add_resource(React_Lecture_mod_del,'/api/lecture/delete',endpoint='react_lecture_delete')
    api_module.add_resource(React_Student,'/api/lecture/studentlist',endpoint='react_student')
    api_module.add_resource(React_Lecture_add,'/api/lecture/create',endpoint='react_lecture_add')
    api_module.add_resource(React_Lecture_mod,'/api/lecture/modify',endpoint='react_lecture_mod')
    api_module.add_resource(React_Prob, '/api/prob/list', endpoint='react_prob')
    api_module.add_resource(React_Prob_del, '/api/prob/delete', endpoint='react_prob_del')
    api_module.add_resource(React_Prob_add, '/api/prob/create', endpoint='react_prob_add')
    api_module.add_resource(React_Prob_mod, '/api/prob/modify', endpoint='react_prob_mod')
    api_module.add_resource(React_Prob_submit_list,'/api/probsubmit/list',endpoint='react_prob_submit_list')
    api_module.add_resource(React_Prob_submit, '/api/prob/submit', endpoint='react_prob_submit')
    api_module.add_resource(Studentgraphlist,'/api/feedback/studentgraphlist',endpoint='studentGraphlist')
    api_module.add_resource(Professorgraphlist,'/api/feedback/professorgraphlist',endpoint='professorgraphlist')
    # api_module.add_resource(Feedback,'/r_feedback',endpoint='r_feedback')
    api_module.add_resource(Feedback2,'/api/feedback',endpoint='feedback2')
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Lecture,'/lecture',endpoint='lecture')
    api_module.add_resource(Admin,'/admin',endpoint='admin')
    api_module.add_resource(Stt, '/stt',endpoint='stt')
    api_module.add_resource(SttJob, '/stt/<jobid>',endpoint='stt_job')
    api_module.add_resource(SttSeq, '/stt/seq', endpoint='stt_seq')
    api_module.add_resource(SttSeqJob, '/stt/seq/<jobid>', endpoint='stt_seq_job')
    api_module.add_resource(Join, '/join', endpoint='join')
    api_module.add_resource(Lecture_mod_del,'/lecture2',endpoint='lecture2')
    api_module.add_resource(Lecture_mod,'/lecture_mod',endpoint='lecture_mod')
    api_module.add_resource(Student,'/student',endpoint='student')
    api_module.add_resource(Major,'/major',endpoint='major')
    api_module.add_resource(Attend,'/attend',endpoint='attend')
    api_module.add_resource(Lecture_add, '/lecture_add', endpoint='lecture_add')
    api_module.add_resource(Prob, '/prob', endpoint='prob')
    api_module.add_resource(Prob_submit, '/prob_submit', endpoint='prob_submit')
    api_module.add_resource(Prob_feedback, '/prob_feedback', endpoint='prob_feedback')
    api_module.add_resource(Prob_add, '/prob_add', endpoint='prob_add')
    api_module.add_resource(prob_upload, '/prob_upload', endpoint='prob_upload')
    api_module.add_resource(Prob_submit_list,'/prob_submit_list',endpoint='prob_submit_list')
    api_module.add_resource(Prob_mod,'/prob_mod',endpoint='prob_mod')
    api_module.add_resource(Admin2,'/admin2',endpoint='admin2')
    api_module.add_resource(Logout,'/logout',endpoint='logout')
    api_module.add_resource(Prob_del,'/prob_del',endpoint='prob_del')
    api_module.add_resource(Email,'/email',endpoint='email')
    api_module.add_resource(Verify_email,'/verify_email',endpoint='verify_email')
