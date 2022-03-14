from .login import Login, LoginRefresh, Account
from .script import ScriptAPI
from .analysis import Analysis

def load_api(api_module):
<<<<<<< HEAD
    #api.add_resource(api,'path',endpoint='엔드포인트 명시')
    api_module.add_resource(Login,'/login',endpoint='login')
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh')
    api_module.add_resource(Account,'/del-account',endpoint='del_account')
    api_module.add_resource(ScriptAPI,'/script/<fname>',endpoint='script_get')
    api_module.add_resource(ScriptAPI,'/script',endpoint='script')
    api_module.add_resource(Analysis,'/analysis',endpoint='analysis')
    #api_module.add_resource(Result,'/result',endpoint='result')
=======
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Account,'/del-account',endpoint='del_account') # DELETE
    api_module.add_resource(ScriptAPI,'/script/<fname>',endpoint='script_get') # GET - DOWNLOAD
    api_module.add_resource(ScriptAPI,'/script',endpoint='script') # POST - UPLOAD
    api_module.add_resource(Analysis,'/analysis',endpoint='analysis')
>>>>>>> 3b16fd49661009d6495ae1a6519a5f01e83ea0ee
