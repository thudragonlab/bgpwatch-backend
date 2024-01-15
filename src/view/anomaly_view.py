from flask import request, Response
import src.service.anomaly_service as anomaly_service
import json
from flask import jsonify

from src import app
from src.view.util import require_api_key
from utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)


@app.route('/events', methods=['get'])
def events():
    event_type = request.args.get('event_type')
    st = request.args.get('st')
    et = request.args.get('et')
    log.debug(f'{st},{et}')
    return jsonify(anomaly_service.events(st, et, event_type))


@app.route('/events/<event_param>', methods=["GET"])
def get_event_detail(event_param):
    return jsonify(anomaly_service.get_event_detail(event_param))


@app.route('/domain_finish', methods=["GET"])
def domain_finish():
    return jsonify(anomaly_service.domain_finish())


@app.route('/get_event_by_condition', methods=["POST"])
@require_api_key
def get_event_by_condition():
    hijack_type = request.json.get('type')
    condition = request.json.get('condition')
    return jsonify(anomaly_service.get_event_by_condition(hijack_type, condition))


@app.route('/get_event_detail', methods=["POST"])
@require_api_key
def get_event_detail_by_api():
    hijack_type = request.json.get('type')
    event_id = request.json.get('event_id')
    return jsonify(anomaly_service.get_event_detail_by_api(hijack_type, event_id))

@app.route('/get_prefix_roa_history', methods=["GET"])
def get_prefix_roa_history():
    prefix = request.args.get('prefix')

    return jsonify(anomaly_service.get_prefix_roa_history(prefix))



