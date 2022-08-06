from flask import Flask, jsonify
from flask_restful import Api
from flasgger import Swagger
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from server.apis import load_api
from server.apis.login import jwt_blocklist
from server import db
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from os import environ as env

app=Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'API Docs',
    'doc_dir': './docs/'
}

"""
sentry_sdk.init(
    dsn="https://c3e83b00ef6843adb8d442a9e438c34d@o1343525.ingest.sentry.io/6618334",#개인에게 할당된 sentry넣기
    integrations=[
        FlaskIntegration(),
    ],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)
"""

app.config['SECRET_KEY'] = 'Shadow-Hunter-nerf-plz'#추후 랜덤문자열로 바꿀것 ㅎㅎ;
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=4)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=1)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{env['SQL_USER']}:{env['SQL_PASSWORD']}@{env['SQL_HOST']}:{env['SQL_PORT']}/{env['SQL_DATABASE']}"
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
    return "MokoKo"

load_api(myApi)
app.run(host='0.0.0.0', port = 5000)