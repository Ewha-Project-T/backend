from flask import Flask
from flask_restful import Api
from flasgger import Swagger
from flask_cors import CORS
from server.apis import load_api

app=Flask(__name__)
CORS(app) # 모든 출처에 대해서 CORS 허용 세세한 설정 추후 논의
myApi=Api(app)
swagger = Swagger(app)

@app.route("/", methods=['GET'])
def hello():
    return "CAT-Secuirty"

load_api(myApi)
app.run(host='0.0.0.0', port = 5000)
