from server.model import Lecture
from .login import Login, LoginRefresh
from .lecture import Lecture
from .admin import admin

def load_api(api_module):
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Lecture,'/lecture',endpoint='lecture')
    api_module.add_resource(admin,'/admin',endpoint='admin')
