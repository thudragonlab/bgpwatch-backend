from src import app
from flask import request
import src.service.user_service as user_service
import json
from flask_httpauth import HTTPTokenAuth
from flask import jsonify
from utils.logger import get_logger, APP_LOG_NAME
from src.service.util import parse_token

log = get_logger(APP_LOG_NAME)

token_auth = HTTPTokenAuth(scheme="Bearer")


@token_auth.verify_token
def verify_token(token):
    try:
        if token:
            parse_token(token)
        else:
            parse_token(bytes(str(request.authorization).split(' ')[1], encoding='UTF-8'))
    except Exception as e:
        log.error(e)
        return False
    return True

@app.route('/register', methods=['GET'])
def register():
    token = request.args.get('token')
    # password = request.form['password']
    # email = request.form['email']
    result = user_service.register_service(token)
    log.debug(f'{result}')
    return jsonify(result)


@app.route('/verifyEmail', methods=['POST'])
def verify_email():
    user_name = request.form['user_name']
    password = request.form['password']
    email = request.form['email']
    result = user_service.verify_email(user_name, password, email, request.origin)
    log.debug(f'{result}')
    log.debug(f'{request}')
    return jsonify(result)


@app.route('/login', methods=['POST'])
def login():
    user_name = request.form['user_name']
    password = request.form['password']
    result = user_service.login_service(user_name, password)
    log.debug(f'{result}')
    return jsonify(result)


@app.route('/forget', methods=['GET'])
def forget():
    userName = request.args.get('userName')
    result = user_service.forget(userName, request.referrer)
    log.debug(f'{result}')
    return jsonify(result)


@app.route('/updatePwd', methods=['POST'])
def updatePwd():
    argsData = json.loads(request.data)
    user = argsData['user']
    pwd = argsData['pwd']
    result = user_service.updatePwd(user, pwd)
    return jsonify(result)


@app.route('/addSourceIp', methods=['GET'])
@token_auth.login_required
def add_source_ip():
    token = request.headers['Authorization']
    source = request.args.get('source')
    result = user_service.add_source_ip(source, token)
    return jsonify(result)


@app.route('/delSourceIp', methods=['GET'])
@token_auth.login_required
def del_source_ip():
    token = request.headers['Authorization']
    source = request.args.get('source')
    result = user_service.del_source_ip(source, token)
    return jsonify(result)


@app.route('/getSourceIP', methods=['GET'])
@token_auth.login_required
def get_source_ip():
    token = request.headers['Authorization']
    result = user_service.get_source_ip(token)
    return jsonify(result)
