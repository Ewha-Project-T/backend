from .login import Login, LoginRefresh, Account, Admin
from .users import Users, PMUsers, MyUsers

def load_api(api_module):
    api_module.add_resource(Admin,'/admin',endpoint='admin')
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Account,'/del-account',endpoint='del_account') # DELETE
    api_module.add_resource(Users,'/users',endpoint='users')
    api_module.add_resource(PMUsers,'/pm-users', endpoint='pm_users')
    api_module.add_resource(Users,'/users/<user_no>',endpoint='users_del')
    api_module.add_resource(MyUsers,'/myinfo',endpoint='one_user_info')

