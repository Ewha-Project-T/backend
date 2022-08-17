import json
from pickle import TRUE
from typing_extensions import Required
from flask import jsonify,render_template, request, redirect, url_for,abort,make_response
from flask_restful import reqparse, Resource
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, get_jwt
)
import re
from ..services.lecture_service import lecture_listing, make_lecture,modify_lecture,delete_lecture, search_student,major_listing,attendee_add,attendee_listing
from ..services.login_service import (
     admin_required, professor_required, assistant_required
)
from os import environ as env
host_url=env["HOST"]
perm_list={"학생":1,"조교":2,"교수":3}

class Assignment(Resource):
    def get(self):#과제 목록
        