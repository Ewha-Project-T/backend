from ..model import Project,User
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

    default_passwd="iy87nSG+BMOjcgssU2mxrB8iwPriXHCj48tCax4uTjT6L2ProGRzo4B+QCRhNMQy9KYw53UhMSoNFf72hlv8nHWhGA8ZoRQOZv69XTME1RF73/PsZy4YowLPOQkznwlSThnpyq3d/HypLVj6CHb80Ym//Dt1stVcQkX5Aceqa0upJj9HbhsfISIPcKtVZF/Les1WXaegkDfCFkOqdAiY7w=="
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
    target_user=User.query.filter_by(id=target_project.project_name+"_USER1").first()#user삭제
    db.session.delete(target_user)
    db.session.commit

    target_pm=User.query.filter_by(id=target_project.project_name+"_PM1").first()#pm삭제
    db.session.delete(target_pm)
    db.session.commit

    db.session.delete(target_project)
    db.session.commit
    return DeleteResult.SUCCESS

def change_project(change_no,name,start,end):
    target_project = Project.query.get(change_no)
    check = Project.query.filter_by(project_name=name).first()
    if(check!=None):
        return ChangeResult.NAME_EXIST
    if(start>end):
        return ChangeResult.INVALID_DATE


    #USER변경
    target_user =User.query.filter_by(id=target_project.project_name+"_USER1").first()
    target_user.id=name+"_USER1"
    db.session.add(target_user)
    db.session.commit

    #PM변경
    target_pm=User.query.filter_by(id=target_project.project_name+"_PM1").first()
    target_pm.id=name+"_PM1"
    db.session.add(target_pm)
    db.session.commit
    
    #프로젝트 변경
    target_project.project_name=name
    target_project.start_date=start
    target_project.end_date=end
    db.session.add(target_project)
    db.session.commit

    return CreateResult.SUCCESS