from flask import Flask, jsonify, redirect, send_from_directory,url_for
from flask_restful import Api
from flasgger import Swagger
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from server.apis import load_api
from server import db
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from os import environ as env
import binascii
from os import urandom

jwt_blocklist=set()
app=Flask(__name__, static_folder='./static')
#cors = CORS(app, resources={r"/*": {"origins": "https://ewaproject-lszyf.run.goorm.site"}},supports_credentials=True)
app.config['SWAGGER'] = {
    'title': 'API Docs',
    'doc_dir': './docs/',
    'openapi': '3.1.0',
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
app.config['SECRET_KEY'] = str(binascii.hexlify(urandom(16)))
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
#app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=1)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{env['SQL_USER']}:{env['SQL_PASSWORD']}@{env['SQL_HOST']}:{env['SQL_PORT']}/{env['SQL_DATABASE']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
app.config['SQLALCHEMY_POOL_SIZE'] = 4000
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['BUNDLE_ERRORS'] = True

db.init_app(app)

with app.app_context():
    db.create_all()

jwt=JWTManager(app)
"""
CORS(app, 
     expose_headers='Location', 
     supports_credentials=True
)
"""
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
@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return unauth_res()

@jwt.unauthorized_loader
def handle_auth_error(e):
    return jsonify({"isAuth":0,"msg":"handle_auth_error"})

@jwt.invalid_token_loader
def custom_invalid_token_callback(e):
    return jsonify({'isauth': 0, "msg":"invalid token"})

"""
    if(e=='Missing cookie "refresh_token_cookie"'):
        return redirect(host_url+ url_for('login'))
    return redirect(host_url + url_for('login_refresh'))
"""
host_url=env["HOST"]

def unauth_res():
    return jsonify({"msg":"invalid token"})

@app.route("/upload/<path:filename>")
def uploads(filename):
    return send_from_directory(env['UPLOAD_PATH'], filename)

@app.route("/", methods=['GET'])
def hello():
    #return redirect('http://203.255.176.34:8080/login')
    return redirect('https://edu-trans.ewha.ac.kr:8443/login')
    #return redirect('https://ewha.ltra.cc/login')

"""
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://ewaproject-lszyf.run.goorm.site'  # 허용할 도메인(들)로 교체하세요
    return response
"""
load_api(myApi)

app.run(host='0.0.0.0', port = 5000, debug=True) 
