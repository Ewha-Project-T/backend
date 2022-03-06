from flask import Flask
from flask_restful import Api
from flasgger import Swagger
from flask_cors import CORS
from server.apis import load_api
import os
from flask_jwt_extended import (JWTManager, jwt_required, create_access_token, get_jwt_identity)
app=Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'API Docs',
    'doc_dir': './docs/'
}
app.config['JWT_SECRET_KEY'] = 'super-secret'
jwt = JWTManager(app) 
CORS(app) # 모든 출처에 대해서 CORS 허용 세세한 설정 추후 논의
myApi=Api(app)
swagger = Swagger(
    app, 
    template_file=r"docs/template.yml",
    parse=False
)
@app.route("/", methods=['GET'])
def hello():
    return "CAT-Secuirty"

load_api(myApi)
app.run(host='0.0.0.0', port = 5000)
