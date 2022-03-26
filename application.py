from flask import Flask, jsonify
from flask_restful import Api
from flasgger import Swagger
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from server.apis import load_api
from server.apis.login import jwt_blocklist
from server import db

app=Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'API Docs',
    'doc_dir': './docs/'
}


app.config['SECRET_KEY'] = 'CAT-Security-King-God'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://cert:cert@203.229.206.16:12344/cert"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 
db.init_app(app)
jwt=JWTManager(app)

CORS(app,expose_headers='Location')
myApi=Api(app, errors=Flask.errorhandler)
swagger = Swagger(
    app, 
    template_file=r"docs/template.yml",
    parse=False
)

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token_in_redis = jti in jwt_blocklist
    return token_in_redis
    
@app.route("/", methods=['GET'])
def hello():
    return "CAT-Secuirty"

load_api(myApi)
app.run(host='0.0.0.0', port = 5000)