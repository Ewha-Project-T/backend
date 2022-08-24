from server.model import Lecture
from .login import Login,Join,Email_check, LoginRefresh, Logout
from .lecture import Attend, Lecture, Lecture_mod, Lecture_mod_del, Student,Major, Lecture_add
from .assignment import Prob, Prob_submit, Prob_feedback,Prob_mod,Prob_add, prob_upload
from .admin import Admin,Admin2
from .stt import Stt, SttJob

def load_api(api_module):
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Lecture,'/lecture',endpoint='lecture')
    api_module.add_resource(Admin,'/admin',endpoint='admin')
    api_module.add_resource(Stt, '/stt',endpoint='stt')
    api_module.add_resource(SttJob, '/stt/<jobid>',endpoint='stt_job')
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
    api_module.add_resource(Email_check,'/mail_check',endpoint='Email_check')
    api_module.add_resource(Prob_mod,'/prob_mod',endpoint='prob_mod')
    api_module.add_resource(Admin2,'/admin2',endpoint='admin2')
    api_module.add_resource(Logout,'/logout',endpoint='logout')
