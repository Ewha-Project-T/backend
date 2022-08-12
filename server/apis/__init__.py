from server.model import Lecture
from .login import Login, LoginRefresh,Join
from .lecture import Attend, Lecture, Lecture_mod_del, Student,Major
from .admin import admin
from .stt import Stt, SttJob

def load_api(api_module):
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Lecture,'/lecture',endpoint='lecture')
    api_module.add_resource(admin,'/admin',endpoint='admin')
    api_module.add_resource(Stt, '/stt',endpoint='stt')
    api_module.add_resource(SttJob, '/stt/<jobid>',endpoint='stt_job')
    api_module.add_resource(Join, '/join', endpoint='join')
    api_module.add_resource(Lecture_mod_del,'/lecture2',endpoint='lecture2')
    api_module.add_resource(Student,'/student',endpoint='student')
    api_module.add_resource(Major,'/major',endpoint='major')
    api_module.add_resource(Attend,'/attend',endpoint='attend')
