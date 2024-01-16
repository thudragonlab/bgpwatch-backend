from flask import request, jsonify
from src.model import user_collection, user_api_collection
from bson import ObjectId
from datetime import datetime
from src.utils.logger import get_logger, APP_LOG_NAME
import functools

inner_log = get_logger(APP_LOG_NAME)


def require_api_key(func):
    @functools.wraps(func)
    def _inner(*args, **kwargs):

        start = datetime.utcnow()
        userObj = None
        try:
            print(userObj)
            userObj = user_collection.find_one({'_id': ObjectId(request.headers.get("KEY"))})
            print(userObj)
            source_ips = userObj['source-ips']
            request_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            print(source_ips)
            print(request_ip)
            if request_ip not in source_ips:
                return jsonify({"status": "error", "message": "not match source ip", "allowed-ips": source_ips, 'request-ip': request_ip}), 401
        except Exception as e:
            inner_log.error(e)
            return jsonify({"status": "error", "message": "Invalid API key."}), 401
        if userObj:
            o = {'user_id': request.headers.get("KEY"), 'url': request.url, 'call-timestamp': start.timestamp(),
                 'source_ip': request_ip}
            try:
                o['json'] = request.json if request.json else {}
            except Exception:
                pass
            if request.data:
                o['data'] = request.data
            if request.args.__dict__:
                o['args'] = request.args

            res = func(*args, **kwargs)
            o['duration'] = datetime.utcnow().timestamp() - start.timestamp()
            user_api_collection.insert_one(o)
            return res
        else:
            return jsonify({"status": "error", "message": "Invalid API key."}), 401

    return _inner
