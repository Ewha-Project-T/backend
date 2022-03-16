from ..model import Project,User
from server import db


class LoginResult:
    SUCCESS = 0
    NAME_EXIST=1
    INVALID_DATE = 2

class DeleteResult:
    SUCCESS = 0
    ALREADY_DELETE=1

def create_project(name,start,end):
    check = Project.query.filter_by(project_name=name).first()
    if(check!=None):
        return LoginResult.NAME_EXIST
    if(start>end):
        return LoginResult.INVALID_DATE
    default_passwd="iy87nSG+BMOjcgssU2mxrB8iwPriXHCj48tCax4uTjT6L2ProGRzo4B+QCRhNMQy9KYw53UhMSoNFf72hlv8nHWhGA8ZoRQOZv69XTME1RF73/PsZy4YowLPOQkznwlSThnpyq3d/HypLVj6CHb80Ym//Dt1stVcQkX5Aceqa0upJj9HbhsfISIPcKtVZF/Les1WXaegkDfCFkOqdAiY7w=="
    #user계정생성    
    acc_user=User(id=name+"_USER1",password=default_passwd,name=name+"_USER1",email=name+"_USER1@email.com")#입력값에 대한 보안처리 해야되나 고민중
    db.session.add(acc_user)
    db.session.commit
    #pm계정 생성
    acc_pm=User(id=name+"_PM1",password=default_passwd,permission=1,name=name+"_PM1",email=name+"_PM1@email.com")#비밀번호 암호화 처리 해야될지 고민중
    db.session.add(acc_pm)
    db.session.commit
    #프로젝트 생성
    acc_pm_no = User.query.filter_by(id=name+"_PM1").first()
    acc=Project(pm_no=acc_pm_no.user_no,project_name=name,start_date=start,end_date=end)
    db.session.add(acc)
    db.session.commit
    return LoginResult.SUCCESS

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