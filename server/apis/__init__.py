from server.apis.react_user import User
from .mail import Email, Verify_email
from .react_feedback import Feedback_graph_update, Feedback_info, Feedback_professor_graph, Feedback_review, Feedback_self_graph, Feedback_self_graph_update, Feedback_self_info, Feedback_self_review, Feedback_self_textae, Feedback_student_graph, Feedback_textae, assignment_zip_down
# from .lecture import Attend, Lecture_mod, Lecture_mod_del,Major, Lecture_add
from .admin import Admin2
from .stt import Stt, SttJob, SttSeq, SttSeqJob
from .react_login import Login2,Logout2,CheckToken,Join2,FindPassword,FindPassword_Check,Find_id
from .react_assignment import React_Cancel_prob, React_Chance_prob, React_Porb_professor, React_Prob_Self,React_Prob_add, React_Prob_calendar, React_Prob_date, React_Prob_detail, React_Prob_end_submission, React_Prob_record, React_Prob_self_detail, React_Prob_self_record, React_Prob_student,React_Prob_submit_list,React_Prob_submit, React_Prob_submit_list2, React_prob_handle, React_self_prob_handle,Studentgraphlist,Professorgraphlist, TranslateAssignment
from .react_login import Login2,Logout2,CheckToken,Join2,FindPassword,FindPassword_Check
from .react_assignment import React_Cancel_prob, React_Cancel_self_prob, React_Chance_prob, React_Porb_professor, React_Prob_Self,React_Prob_add, React_Prob_detail, React_Prob_end_submission, React_Prob_record, React_Prob_self_detail, React_Prob_self_end_submission, React_Prob_self_record, React_Prob_self_submit, React_Prob_student,React_Prob_submit_list,React_Prob_submit, React_Prob_submit_list2, React_prob_handle, React_self_prob_handle,Studentgraphlist,Professorgraphlist, TranslateAssignment, TranslateSelfAssignment, prob_upload, prob_upload_file
from .react_lecture import React_Lecture, React_Lecture_apply_list, React_Lecture_enrolment,React_Lecture_mod_del, React_Lecture_request,React_Student,React_Lecture_add,React_Lecture_mod, React_Students



def load_api(api_module):
    api_module.add_resource(User,'/api/user',endpoint='user') # GET POST PUT PATCH DELETE
    api_module.add_resource(Join2,'/api/user/join',endpoint='join2') # GET POST PUT PATCH DELETE
    api_module.add_resource(React_Student,'/api/lecture/studentlist',endpoint='react_student')
    api_module.add_resource(React_Prob_submit_list,'/api/probsubmit/list',endpoint='react_prob_submit_list')
    
    api_module.add_resource(Studentgraphlist,'/api/feedback/studentgraphlist',endpoint='studentGraphlist')
    api_module.add_resource(Professorgraphlist,'/api/feedback/professorgraphlist',endpoint='professorgraphlist')
    api_module.add_resource(Email,'/api/user/email',endpoint='email')
    api_module.add_resource(Verify_email,'/api/user/verify_email',endpoint='verify_email')
    api_module.add_resource(Find_id,'/api/user/find_id',endpoint='find_id')
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
    api_module.add_resource(React_Prob_Self, '/api/prob/self', endpoint='react_prob_self')
    api_module.add_resource(React_self_prob_handle, '/api/prob/self/handle', endpoint='react_self_prob_handle')
    api_module.add_resource(React_Prob_self_detail, '/api/prob/self/detail', endpoint='react_self_prob_detail')
    api_module.add_resource(React_Prob_self_record, '/api/prob/self/record', endpoint='react_self_Prob_record')
    api_module.add_resource(React_Prob_self_submit, '/api/prob/self/submit', endpoint='react_self_prob_submit')
    api_module.add_resource(React_Prob_self_end_submission, '/api/prob/self/end', endpoint='React_self_Prob_end_submission')
    api_module.add_resource(React_Cancel_self_prob, '/api/prob/self/cancel', endpoint='react_self_prob_cancel')
    api_module.add_resource(Feedback_self_info, '/api/prob/self/info', endpoint='Feedback_self_info')
    api_module.add_resource(Feedback_self_textae, '/api/prob/self/textae', endpoint='Feedback_self_textae')
    api_module.add_resource(Feedback_self_review, '/api/prob/self/review', endpoint='react_self_prob_review')
    api_module.add_resource(TranslateSelfAssignment, '/api/prob/self/translate', endpoint='react_self_Prob_translate')
    api_module.add_resource(Feedback_self_graph, '/api/prob/self/graph', endpoint='feedback_self_graph')
    api_module.add_resource(Feedback_self_graph_update, '/api/prob/self/graph/update', endpoint='feedback_self_graph_update')

    api_module.add_resource(React_Prob_calendar, '/api/calendar', endpoint='react_calendar')
    api_module.add_resource(React_Prob_date, '/api/calendar/prob', endpoint='react_date')
    api_module.add_resource(React_Lecture_enrolment, '/api/lecture/code', endpoint='react_lecture_enrolment')
    api_module.add_resource(React_Lecture_request, '/api/lecture/request', endpoint='react_lecture_request')
    api_module.add_resource(React_Lecture_apply_list, '/api/lecture/apply', endpoint='react_lecture_apply_list')
    api_module.add_resource(React_Students, '/api/lecture/students', endpoint='react_students')
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
    #api_module.add_resource(React_Prob_del, '/api/prob/delete', endpoint='react_prob_del')
    api_module.add_resource(React_Lecture_add,'/api/lecture/create',endpoint='react_lecture_add')
    api_module.add_resource(React_Lecture_mod,'/api/lecture/modify',endpoint='react_lecture_mod')
    api_module.add_resource(React_Lecture_mod_del,'/api/lecture/delete',endpoint='react_lecture_delete')

    #비밀번호변경
    api_module.add_resource(FindPassword,'/api/user/findpass',endpoint='findpassword') # GET POST PUT PATCH DELETE
    api_module.add_resource(FindPassword_Check,'/api/user/findpass_check',endpoint='findpassword_check') 
    
    api_module.add_resource(SttJob, '/stt/<jobid>',endpoint='stt_job')
    api_module.add_resource(SttSeq, '/stt/seq', endpoint='stt_seq')
    api_module.add_resource(SttSeqJob, '/stt/seq/<jobid>', endpoint='stt_seq_job')
    # api_module.add_resource(Lecture_mod_del,'/lecture2',endpoint='lecture2')
    # api_module.add_resource(Lecture_mod,'/lecture_mod',endpoint='lecture_mod')
    # api_module.add_resource(Major,'/major',endpoint='major')
    # api_module.add_resource(Attend,'/attend',endpoint='attend')
    # api_module.add_resource(Lecture_add, '/lecture_add', endpoint='lecture_add')
    api_module.add_resource(Admin2,'/admin2',endpoint='admin2')