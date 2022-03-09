from flask import jsonify
from flask_restful import reqparse, Resource
from ..services.login_service import login_required

class ScriptAPI(Resource):
    @login_required()
    def get(self):
        return {"msg":"scriptAPI"}, 200