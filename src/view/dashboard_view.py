from flask import request
import src.service.dashboard_service as dashboard_service
from flask import jsonify
from src import app
from utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)


@app.route('/prefix_list', methods=['get'])
def get_prefix_list():
    asn = request.args.get("asn")
    query_str = request.args.get("qstr")
    log.debug(f'{query_str},{asn}')
    return jsonify(dashboard_service.get_prefix_list(asn, query_str))


@app.route('/peer_list', methods=['get'])
def get_peer_list():
    asn = request.args.get("asn")
    ipversion = request.args.get("ipversion")
    return jsonify(dashboard_service.get_peer_list(asn, ipversion))


@app.route('/route_history_stats', methods=['get'])
def get_route_history_stats():
    qtype = "g" if request.args.get("qtype") is None else request.args.get("qtype")  # "g" for glance, "f" for focus
    asns = request.args.get("asns")
    dur = 7 if request.args.get("dur") is None else int(request.args.get("dur"))  # duration in days
    return jsonify(dashboard_service.get_route_history_stats(qtype, asns, dur))

@app.route('/get_whois_info_by_asn', methods=['get'])
def get_whois_info_by_asn():
    asn = request.args.get("asn")
    return jsonify(dashboard_service.get_whois_info_by_asn(asn))

