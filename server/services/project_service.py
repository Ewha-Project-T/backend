from ..model import Project,User, PROJECT_SCRIPT, Script
from server import db


class CreateResult:
    SUCCESS = 0
    NAME_EXIST=1
    INVALID_DATE = 2
class ChangeResult:
    SUCCESS = 0
    NAME_EXIST=1
    INVALID_DATE = 2
class DeleteResult:
    SUCCESS = 0
    ALREADY_DELETE=1
class EnrollResult:
    SUCCESS = 0
    INVALID_SCRIPT_NO = 1
    DUPLICATED_SCRIPT = 2
class DeleteScriptResult:
    SUCCESS = 0
    INVALID_SCRIPT_NO = 1
    INVALID_PROJECT_NO = 2

def create_project(name,start,end):
    check = Project.query.filter_by(project_name=name).first()
    if(check!=None):
        return CreateResult.NAME_EXIST
    if(start>end):
        return CreateResult.INVALID_DATE

    #프로젝트 생성
    acc=Project(project_name=name,start_date=start,end_date=end)
    db.session.add(acc)
    db.session.commit

    default_passwd="1234"
    my_pro = Project.query.filter_by(project_name=name).first()
    #user계정생성    
    acc_user=User(id=name+"_USER1",password=default_passwd,name=name+"_USER1",email=name+"_USER1@email.com",project_no=my_pro.project_no)#입력값에 대한 보안처리 해야되나 고민중
    db.session.add(acc_user)
    db.session.commit
    #pm계정 생성
    acc_pm=User(id=name+"_PM1",password=default_passwd,permission=1,name=name+"_PM1",email=name+"_PM1@email.com",project_no=my_pro.project_no)
    db.session.add(acc_pm)
    db.session.commit
    
    return CreateResult.SUCCESS

def delete_project(del_no):
    target_project = Project.query.get(del_no)
    if(target_project==None):
        return DeleteResult.ALREADY_DELETE
    target_acc=User.query.filter_by(project_no=target_project.project_no).first()
    if(target_acc!=None):
        db.session.delete(target_acc)
        db.session.commit

    db.session.delete(target_project)
    db.session.commit
    return DeleteResult.SUCCESS

def change_project(change_no, name, start, end):
    target_project = Project.query.filter_by(project_no=change_no).first()
    check = Project.query.filter_by(project_name=name).first()
    if(check!=None):
        if(check.project_no != int(change_no)):
            return ChangeResult.NAME_EXIST
    if(start>end):
        return ChangeResult.INVALID_DATE


    #USER변경
    target_user = User.query.filter_by(id=target_project.project_name+"_USER1").first()
    if(target_user != None):
        target_user.id=name+"_USER1"
        target_user.name=name+"_USER1"
        target_user.email=name+"_USER1@email.com"
        db.session.add(target_user)
        db.session.commit

    #PM변경
    target_pm=User.query.filter_by(id=target_project.project_name+"_PM1").first()
    if(target_pm != None):
        target_pm.id=name+"_PM1"
        target_pm.name=name+"_PM1"
        target_pm.email=name+"_PM1@email.com"
        db.session.add(target_pm)
        db.session.commit
    
    #프로젝트 변경
    target_project.project_name=name
    target_project.start_date=start
    target_project.end_date=end
    db.session.add(target_project)
    db.session.commit

    return CreateResult.SUCCESS

def listing_project():
    project_list = Project.query.all()
    project_list_result = []
    for proj in project_list:
        tmp = {}
        tmp["proj_no"] = vars(proj)["project_no"]
        tmp["project_name"] = vars(proj)["project_name"]
        tmp["start_date"] = vars(proj)["start_date"]
        tmp["end_date"] = vars(proj)["end_date"]
        project_list_result.append(tmp)
    return project_list_result

def enroll_project_scripts(project_no, script_no):
    script = Script.query.filter_by(id=script_no).first()
    if(script==None):
        return EnrollResult.INVALID_SCRIPT_NO
    project_script = PROJECT_SCRIPT.query.filter_by(project_no=project_no, script_no=script.id).first()
    if(project_script!=None):
        return EnrollResult.DUPLICATED_SCRIPT
    new_script = PROJECT_SCRIPT(project_no=project_no, type=script.type, script_name=script.script_name, script_no=script.id)
    db.session.add(new_script)
    db.session.commit
    return EnrollResult.SUCCESS

def delete_project_scripts(project_no, script_no):
    script = PROJECT_SCRIPT.query.filter_by(no=script_no).first()
    if(script == None):
        return DeleteScriptResult.INVALID_SCRIPT_NO
    project_script = PROJECT_SCRIPT.query.filter_by(project_no=project_no, no=script_no).first()
    if(project_script == None):
        return DeleteScriptResult.INVALID_PROJECT_NO
    db.session.delete(project_script)
    db.session.commit
    return DeleteScriptResult.SUCCESS