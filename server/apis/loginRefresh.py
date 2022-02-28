from flask_restful import reqparse, Resource

# token refreshing API
class LoginRefresh(Resource):
    def get(self):
        return {
            "status": "success"
        }, 200