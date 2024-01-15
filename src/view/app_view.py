from flask import request, Response, render_template,redirect
import src.service.app_service as app_service
import json
from flask import jsonify
from src import app
# from utils.logger import get_logger, APP_LOG_NAME
from src.view.util import require_api_key

# log = get_logger(APP_LOG_NAME)


@app.route('/getAsRoute', methods=['GET'])
def get_providers():
    asn = request.args.get('asn')
    col_type = request.args.get('type')
    return jsonify(app_service.get_providers_service(asn, col_type))


@app.route('/getPeerTypeDistribute', methods=['GET'])
def get_peer_type_distribute():
    asn = request.args.get('asn')
    return jsonify(app_service.get_peer_type_distribute_service(asn))


@app.route('/getAsInfoByList', methods=['post'])
def get_as_info_by_list():
    asn_list = json.loads(request.get_data(as_text=True))
    return jsonify(app_service.get_as_info_by_list_service(asn_list))


@app.route('/asInfo', methods=['get'])
def as_info():
    asn = request.args.get('asn')
    return jsonify(app_service.asinfo_service(asn))


@app.route('/getRealTimeDataInAWhile', methods=['get'])
def get_real_time_a_while():
    return jsonify(app_service.get_real_time_in_a_while_service())


@app.route('/getRealTimeData', methods=['get'])
def get_real_time():
    return jsonify(app_service.get_real_time_data_by_second())


@app.route('/getAsList', methods=['get'])
def get_as_list():
    asn = request.args.get('asn')
    return jsonify(app_service.get_as_list(asn))


@app.route('/getAsPathByPrefix', methods=['get'])
def get_as_path_by_prefix():
    prefix = request.args.get('prefix')
    asn = request.args.get('asn')
    _type = request.args.get('type')
    return jsonify(app_service.get_as_path_by_prefix(prefix, asn, _type))


@app.route('/getResilienceByccCode', methods=['get'])
def get_resilience_by_cc_code():
    cc = request.args.get('cc')
    return jsonify(app_service.get_resilience_by_cc_code(cc))


@app.route('/getPrefixTotalByAsn', methods=['get'])
def get_prefix_total_by_asn():
    asn = request.args.get('asn')
    return jsonify(app_service.get_prefix_total_by_asn(asn))


@app.route('/downLoadASDiff', methods=['get'])
def down_load_as_diff():
    url = request.args.get('url')
    file_content, file_name = app_service.down_load_as_diff(url)
    response = Response(file_content, content_type='application/octet-stream')
    response.headers["Content-disposition"] = 'attachment; filename=%s' % file_name
    return response


@app.route('/getTopologyData', methods=['get'])
def get_topology_data():
    cc = request.args.get('cc')
    asn = request.args.get('asn')
    return jsonify(app_service.get_topology_data(cc, asn))


@app.route('/getTopologyDataOpt', methods=['get'])
def get_topology_data_optimize():
    cc = request.args.get('cc')
    asn = request.args.get('asn')
    return jsonify(app_service.get_topology_data_optimize(cc, asn))


@app.route('/getAsByCc', methods=['get'])
def get_as_by_cc():
    cc = request.args.get('cc')
    return jsonify(app_service.get_as_by_cc(cc))


# @app.route('/getRtreeByAsn', methods=['get'])
# def get_rtree_by_asn():
#     asn = request.args.get('asn')
#     cc = request.args.get('cc')
#     cone_condition = request.args.get('condition')
#     log.debug(f'asn -> {asn},cc -> {cc}, cone_condition -> {cone_condition}')
#     return jsonify(app_service.get_rtree_by_asn(cc, asn, cone_condition))


@app.route('/getRtreeByPrefix', methods=['get'])
def get_rtree_by_prefix():
    prefix = request.args.get('prefix')
    return jsonify(app_service.get_rtree_by_prefix(prefix))


@app.route('/getRouteByIP', methods=['get'])
def get_route_by_prefix():
    # IP <--> IP
    left_ip = request.args.get('left_ip')
    right_ip = request.args.get('right_ip')
    # log.debug(f'{left_ip},{right_ip}')
    return jsonify(app_service.get_route_by_prefix(left_ip, right_ip))


@app.route('/getAsInfo', methods=['get'])
def getAsInfo():
    asn = request.args.get('asn')
    as_name = request.args.get('as_name')
    org_name = request.args.get('org_name')
    return jsonify(app_service.getAsInfo(asn, as_name, org_name))


@app.route('/doc', methods=['get'])
def doc():
    # print(app.jinja_loader.searchpath[0])
    # return render_template('redoc-static.html')
    return redirect('https://apifox.com/apidoc/shared-79066bdd-eb95-4e0f-9131-a3284d1825b0', code=301)



@app.route('/myapi', methods=['get'])
@require_api_key
def docc():
    print(app.jinja_loader.searchpath[0])
    return render_template('redoc-static.html')
