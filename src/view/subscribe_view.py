from src import app
from flask import request
import src.service.subscribe_service as subscribe_service
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


@app.route('/add_as_with_list', methods=['post'])
@token_auth.login_required
def add_as_with_list():
    token = request.headers['Authorization']
    as_list = request.json.get('as_list')
    return jsonify(subscribe_service.add_as_with_list(token, as_list))


@app.route('/del_as_in_list', methods=['put'])
@token_auth.login_required
def del_as_in_list():
    token = request.headers['Authorization']
    as_list = request.json.get('as_list')
    return jsonify(subscribe_service.del_as_in_list(token, as_list))


@app.route('/get_subscribed_by_token', methods=['get'])
@token_auth.login_required
def get_subscribed_by_token():
    app.logger.info(request.headers)
    token = request.headers['Authorization']
    return jsonify(subscribe_service.get_subscribed_by_token(token))


@app.route('/get_hijack_event', methods=['post'])
@token_auth.login_required
def get_hijack_event():
    app.logger.info(request.headers)
    token = request.headers['Authorization']
    st = request.json.get('st')
    et = request.json.get('et')
    # print(st,et,'?')
    return jsonify(subscribe_service.get_hijack_event(token, st, et))


@app.route('/confirm_event', methods=['get'])
def confirm_event():
    app.logger.info(request.headers)
    token = request.headers['Authorization']
    event_id = request.args.get('_id')
    event_type = request.args.get('event_type')
    description = request.args.get('description')
    return jsonify(subscribe_service.confirm_event(event_id, event_type, token, description))


@app.route('/unconfirmed_event', methods=['get'])
@token_auth.login_required
def unconfirmed_event():
    app.logger.info(request.headers)
    token = request.headers['Authorization']
    event_id = request.args.get('_id')
    event_type = request.args.get('event_type')
    return jsonify(subscribe_service.unconfirmed_event(event_id, event_type, token))


@app.route('/reject_event', methods=['post'])
def reject_event():
    token = request.headers['Authorization']
    event_id = request.json.get('_id')
    event_type = request.json.get('event_type')
    reason = request.json.get('reason')
    return jsonify(subscribe_service.reject_event(event_id, event_type, reason, token))


@app.route('/un_reject_event', methods=['post'])
@token_auth.login_required
def un_reject_event():
    token = request.headers['Authorization']
    event_id = request.json.get('_id')
    event_type = request.json.get('event_type')
    return jsonify(subscribe_service.un_reject_event(event_id, event_type, token))


@app.route('/get_peer_diff', methods=['post'])
@token_auth.login_required
def get_peer_diff():
    token = request.headers['Authorization']
    return jsonify(subscribe_service.get_peer_diff(token))


@app.route('/add_sub_comment', methods=['post'])
@token_auth.login_required
def add_sub_comment():
    token = request.headers['Authorization']
    event_id = request.json.get('_id')
    event_type = request.json.get('event_type')
    parent_user_id = request.json.get('user_id')
    comment = request.json.get('comment')
    reply_user = request.json.get('reply_user')
    print(reply_user)
    return jsonify(subscribe_service.add_sub_comment(event_id, event_type, comment, parent_user_id, token, reply_user))


@app.route('/del_sub_comment', methods=['post'])
@token_auth.login_required
def del_sub_comment():
    token = request.headers['Authorization']
    event_id = request.json.get('_id')
    event_type = request.json.get('event_type')
    parent_user_id = request.json.get('user_id')
    comment_id = request.json.get('comment_id')
    return jsonify(subscribe_service.del_sub_comment(event_id, event_type, comment_id, parent_user_id, token))


@app.route('/get_peer_stats', methods=['post'])
@token_auth.login_required
def get_peer_stats():
    token = request.headers['Authorization']
    return jsonify(subscribe_service.get_peer_stats(token))


@app.route('/search_as2prefix_path', methods=['post'])
@token_auth.login_required
def search_as2prefix_path():
    token = request.headers['Authorization']
    # asn = request.json.get('asn')
    # prefix = request.json.get('prefix')
    return jsonify(subscribe_service.search_as2prefix_path(token))


@app.route('/search_as2prefix_path_info', methods=['post'])
@token_auth.login_required
def search_as2prefix_path_info():
    token = request.headers['Authorization']
    # asn = request.json.get('asn')
    # prefix = request.json.get('prefix')
    return jsonify(subscribe_service.search_as2prefix_path_info(token))


@app.route('/get_as2prefix_path', methods=['post'])
def get_as2prefix_path():
    asn = request.json.get('asn')
    prefix = request.json.get('prefix')
    return jsonify(subscribe_service.get_as2prefix_path(asn, prefix))


@app.route('/add_prefix_subscribe', methods=['post'])
@token_auth.login_required
def add_prefix_subscribe():
    token = request.headers['Authorization']
    asn = request.json.get('asn')
    prefix = request.json.get('prefix')
    return jsonify(subscribe_service.add_prefix_subscribe(asn, prefix, token))


@app.route('/remove_as2prefix_path', methods=['post'])
@token_auth.login_required
def remove_as2prefix_path():
    token = request.headers['Authorization']
    asn = request.json.get('asn')
    prefix = request.json.get('prefix')
    return jsonify(subscribe_service.remove_as2prefix_path(str(asn), prefix, token))
