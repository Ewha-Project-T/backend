from server.apis.mail import Email, Verify_email
from .react_feedback import Feedback_graph_update, Feedback_info, Feedback_professor_graph, Feedback_review, Feedback_student_graph, Feedback_textae, assignment_zip_down
from .login import Login,Join, LoginRefresh, Logout
from .lecture import Attend, Lecture, Lecture_mod, Lecture_mod_del, Student,Major, Lecture_add
from .assignment import Prob, Prob_del, Prob_submit, Prob_feedback,Prob_mod,Prob_add, prob_upload, Prob_submit_list, prob_upload_file
from .admin import Admin,Admin2
from .stt import Stt, SttJob, SttSeq, SttSeqJob
from .react_login import Login2,Logout2,CheckToken,Join2,FindPassword,FindPassword_Check
from .react_assignment import React_Cancel_prob, React_Chance_prob, React_Porb_professor,React_Prob_add, React_Prob_detail, React_Prob_end_submission, React_Prob_record, React_Prob_student,React_Prob_submit_list,React_Prob_submit, React_Prob_submit_list2, React_prob_handle,Studentgraphlist,Professorgraphlist, TranslateAssignment
from .react_lecture import React_Lecture,React_Lecture_mod_del,React_Student,React_Lecture_add,React_Lecture_mod



def load_api(api_module):
    api_module.add_resource(Join2,'/api/user/join',endpoint='join2') # GET POST PUT PATCH DELETE
    api_module.add_resource(React_Student,'/api/lecture/studentlist',endpoint='react_student')
    api_module.add_resource(React_Prob_submit_list,'/api/probsubmit/list',endpoint='react_prob_submit_list')
    
    api_module.add_resource(Studentgraphlist,'/api/feedback/studentgraphlist',endpoint='studentGraphlist')
    api_module.add_resource(Professorgraphlist,'/api/feedback/professorgraphlist',endpoint='professorgraphlist')

    ############################
    ###########신규 추가##########
    ############################
    api_module.add_resource(React_prob_handle, '/api/prob/handle', endpoint='react_prob_handle') 
    api_module.add_resource(React_Prob_submit_list2, '/api/feedback/manage', endpoint='react_prob_submit_list2')
    api_module.add_resource(Feedback_textae,'/api/feedback/textae',endpoint='Feedback_textae')
    api_module.add_resource(Feedback_info,'/api/feedback/info', endpoint='Feedback_info') # 과제 피드백 과제 및 학생 정보
    api_module.add_resource(React_Prob_detail, '/api/prob/detail', endpoint='react_prob_detail') #
    api_module.add_resource(React_Prob_student, '/api/prob/student', endpoint='react_prob_student') #
    api_module.add_resource(React_Porb_professor, '/api/prob/professor', endpoint='react_prob_professor') #
    api_module.add_resource(prob_upload_file, '/api/prob_upload_file', endpoint='prob_upload_file') #
    api_module.add_resource(React_Prob_record, '/api/prob/record', endpoint='react_Prob_record') #
    api_module.add_resource(React_Prob_end_submission, '/api/prob/end', endpoint='React_Prob_end_submission') #
    api_module.add_resource(Feedback_review, '/api/feedback/review', endpoint='react_prob_review')
    api_module.add_resource(React_Cancel_prob, '/api/prob/cancel', endpoint='react_prob_cancel')
    api_module.add_resource(React_Chance_prob, '/api/prob/chance', endpoint='react_prob_chance')

    api_module.add_resource(TranslateAssignment, '/api/prob/translate', endpoint='react_Prob_translate')
    api_module.add_resource(React_Prob_submit, '/api/prob/submit', endpoint='react_prob_submit')
    api_module.add_resource(Feedback_professor_graph, '/api/feedback/professor/graph', endpoint='feedback_professor_graph')
    api_module.add_resource(Feedback_student_graph, '/api/feedback/student/graph', endpoint='feedback_student_graph')
    api_module.add_resource(Feedback_graph_update, '/api/feedback/graph/update', endpoint='feedback_graph_update')
    api_module.add_resource(assignment_zip_down,'/api/feedback/json',endpoint='assignment_zip_down')#zip 다운로드
    ############################
    ######옛날 것인데 사용중########
    ############################
    api_module.add_resource(Login2,'/api/user/login',endpoint='login2') # GET POST PUT PATCH DELETE
    api_module.add_resource(React_Lecture,'/api/lecture/list',endpoint='react_lecture_list')
    api_module.add_resource(Logout2,'/api/user/logout',endpoint='logout2') # GET POST PUT PATCH DELETE
    api_module.add_resource(prob_upload, '/api/prob_upload', endpoint='prob_upload')
    api_module.add_resource(Stt, '/api/stt',endpoint='stt')
    api_module.add_resource(CheckToken,'/api/user/auth',endpoint='checkToken') 

    ############################
    #######추후 삭제 예정##########
    ############################
    #api_module.add_resource(React_Prob_mod, '/api/prob/modify', endpoint='react_prob_mod')
    api_module.add_resource(React_Prob_add, '/api/prob/create', endpoint='react_prob_add')
    # api_module.add_resource(Feedback,'/r_feedback',endpoint='r_feedback')
    api_module.add_resource(Login,'/login',endpoint='login') # GET POST PUT PATCH DELETE
    #api_module.add_resource(React_Prob_del, '/api/prob/delete', endpoint='react_prob_del')
    api_module.add_resource(React_Lecture_add,'/api/lecture/create',endpoint='react_lecture_add')
    api_module.add_resource(React_Lecture_mod,'/api/lecture/modify',endpoint='react_lecture_mod')
    api_module.add_resource(React_Lecture_mod_del,'/api/lecture/delete',endpoint='react_lecture_delete')

    #비밀번호변경
    api_module.add_resource(FindPassword,'/api/user/findpass',endpoint='findpassword') # GET POST PUT PATCH DELETE
    api_module.add_resource(FindPassword_Check,'/api/user/findpass_check',endpoint='findpassword_check') 
    api_module.add_resource(LoginRefresh,'/login-refresh',endpoint='login_refresh') 
    api_module.add_resource(Lecture,'/lecture',endpoint='lecture')
    api_module.add_resource(Admin,'/admin',endpoint='admin')
    
    api_module.add_resource(SttJob, '/stt/<jobid>',endpoint='stt_job')
    api_module.add_resource(SttSeq, '/stt/seq', endpoint='stt_seq')
    api_module.add_resource(SttSeqJob, '/stt/seq/<jobid>', endpoint='stt_seq_job')
    api_module.add_resource(Join, '/join', endpoint='join')
    api_module.add_resource(Lecture_mod_del,'/lecture2',endpoint='lecture2')
    api_module.add_resource(Lecture_mod,'/lecture_mod',endpoint='lecture_mod')
    api_module.add_resource(Student,'/student',endpoint='student')
    api_module.add_resource(Major,'/major',endpoint='major')
    api_module.add_resource(Attend,'/attend',endpoint='attend')
    api_module.add_resource(Lecture_add, '/lecture_add', endpoint='lecture_add')
    api_module.add_resource(Prob, '/prob', endpoint='prob')
    api_module.add_resource(Prob_submit, '/prob_submit', endpoint='prob_submit')
    api_module.add_resource(Prob_feedback, '/prob_feedback', endpoint='prob_feedback')
    api_module.add_resource(Prob_add, '/prob_add', endpoint='prob_add')
    api_module.add_resource(Prob_submit_list,'/prob_submit_list',endpoint='prob_submit_list')
    api_module.add_resource(Prob_mod,'/prob_mod',endpoint='prob_mod')
    api_module.add_resource(Admin2,'/admin2',endpoint='admin2')
    api_module.add_resource(Logout,'/logout',endpoint='logout')
    api_module.add_resource(Prob_del,'/prob_del',endpoint='prob_del')
    api_module.add_resource(Email,'/email',endpoint='email')
    api_module.add_resource(Verify_email,'/verify_email',endpoint='verify_email')