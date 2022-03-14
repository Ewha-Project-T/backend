from .login import Login, LoginRefresh, Account
from .script import ScriptAPI
from .analysis import Analysis
from .result import Result

def load_api(api_module):
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Account,'/del-account',endpoint='del_account') # DELETE
    api_module.add_resource(ScriptAPI,'/script/<fname>',endpoint='script_get') # GET - DOWNLOAD
    api_module.add_resource(ScriptAPI,'/script',endpoint='script') # POST - UPLOAD
    api_module.add_resource(Analysis,'/analysis',endpoint='analysis')
    api_module.add_resource(Result,'/result',endpoint='result')
