from flask import jsonify
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required

class Scan(Resource):
    @jwt_required()
    def get(self):
        return {"msg":"scanAPI"}, 200