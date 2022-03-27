from .login import Login, LoginRefresh, Account, Admin
from .script import ScriptAPI, ScriptListingAPI, AdminScript
from .analysis import Analysis, Hosts
from .project import Project, ProjectList
from .parser import XML_Parser
from .users import Users

def load_api(api_module):
    api_module.add_resource(Admin,'/admin',endpoint='admin')
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Account,'/del-account',endpoint='del_account') # DELETE
    api_module.add_resource(ScriptAPI,'/script/<fname>',endpoint='script_get') # GET - DOWNLOAD
    api_module.add_resource(ScriptAPI,'/script',endpoint='script') # POST - UPLOAD
    api_module.add_resource(ScriptListingAPI,'/script-list',endpoint='script_list')
    api_module.add_resource(AdminScript,'/scripts',endpoint='admin_scripts')
    api_module.add_resource(Analysis,'/analysis',endpoint='analysis')
    api_module.add_resource(Project,'/project',endpoint='project')
    api_module.add_resource(Project,'/project/<project_no>',endpoint='project_del-patch')
    api_module.add_resource(ProjectList, '/project-list', endpoint='project_list')
    api_module.add_resource(XML_Parser,'/parser',endpoint='parser')
    api_module.add_resource(Users,'/users',endpoint='users')
    api_module.add_resource(Users,'/users/<user_no>',endpoint='users_del')
    api_module.add_resource(Hosts,'/hosts/<proj_no>',endpoint='hosts_list')
    

