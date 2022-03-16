from .login import Login, LoginRefresh, Account
from .script import ScriptAPI, ScriptListingAPI
from .analysis import Analysis
from .project import Project
from .parser import XML_Parser
<<<<<<< HEAD

=======
>>>>>>> c81623c9640b19b6ff2ed65dce3da555f9c2dae8

def load_api(api_module):
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Account,'/del-account',endpoint='del_account') # DELETE
    api_module.add_resource(ScriptAPI,'/script/<fname>',endpoint='script_get') # GET - DOWNLOAD
    api_module.add_resource(ScriptAPI,'/script',endpoint='script') # POST - UPLOAD
    api_module.add_resource(Analysis,'/analysis/<filename>',endpoint="analysis_get") # download
    api_module.add_resource(Analysis,'/analysis',endpoint='analysis')
    api_module.add_resource(Project,'/project',endpoint='project')
    api_module.add_resource(Project,'/project/<project_no>',endpoint='project_del')
    api_module.add_resource(XML_Parser,'/parser',endpoint='parser')
    api_module.add_resource(ScriptListingAPI,'/script-list',endpoint='script_list')
<<<<<<< HEAD

=======
    
>>>>>>> acde3df7364b6d2bed231a04336b8836477a56e1
