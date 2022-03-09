from .login import Login
from .loginRefresh import LoginRefresh
from .login import Account
from .script import ScriptAPI
from .analysis import Analysis

def load_api(api_module):
    #api.add_resource(api,'path',endpoint='엔드포인트 명시')
    api_module.add_resource(Login,'/login',endpoint='login')
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh')
    api_module.add_resource(Account,'/del-account',endpoint='del_account')
    api_module.add_resource(ScriptAPI,'/script/<fname>',endpoint='script_get')
    api_module.add_resource(ScriptAPI,'/script',endpoint='script')
    api_module.add_resource(Analysis,'/analysis',endpoint='analysis')