from .login import Login
from .loginRefresh import LoginRefresh

def load_api(api_module):
    #api.add_resource(api,'path',endpoint='엔드포인트 명시')
    api_module.add_resource(Login,'/login',endpoint='login')
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh')
