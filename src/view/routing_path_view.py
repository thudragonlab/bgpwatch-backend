from flask import request
import src.service.routing_path_service as routing_path_service
from flask import jsonify

from src import app


@app.route('/getRtreeByPrefixData', methods=['get'])
def get_rtree_by_prefix_data():
    prefix = request.args.get('prefix')
    return jsonify(routing_path_service.get_rtree_by_prefix(prefix))


@app.route('/getRtreeByPrefixDataToTopo', methods=['get'])
def get_rtree_by_prefix_data_to_topo():
    prefix = request.args.get('prefix')
    return jsonify(routing_path_service.get_rtree_by_prefix_data_to_topo(prefix))


@app.route('/getRoutingPathCluster', methods=['get'])
def get_routing_path_cluster():
    asn = request.args.get('asn')
    return jsonify(routing_path_service.get_routing_path_cluster(asn))


@app.route('/getRtreeByHash', methods=['get'])
def get_rtree_by_hash():
    _hash = request.args.get('hash')
    return jsonify(routing_path_service.get_rtree_by_hash(_hash))


@app.route('/getRtreeByHashes', methods=['post'])
def get_rtree_by_hashes():
    hashes = request.json
    asn = request.args.get('asn')
    return jsonify(routing_path_service.get_rtree_by_hashes(hashes, asn))


@app.route('/getBiPrefixByAnotherPrefix', methods=['get'])
def get_bi_prefix_by_another_prefix():
    prefix = request.args.get('prefix')
    return jsonify(routing_path_service.get_bi_prefix_by_another_prefix(prefix))


@app.route('/getJitterTopNPrefixByAs', methods=['get'])
def get_jitter_top_n_prefix_by_as():
    asn = request.args.get('asn')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')

    return jsonify(routing_path_service.get_jitter_top_n_prefix_by_as(asn, st, et, source))


@app.route('/getJitterTopNPrefixByAsAndPfx', methods=['get'])
def get_jitter_top_n_prefix_by_as_and_pfx():
    asn = request.args.get('asn')
    st = request.args.get('st')
    et = request.args.get('et')
    pfx = request.args.get('prefix')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_top_n_prefix_by_as_and_pfx(asn, pfx, st, et, source))


@app.route('/getJitterDataByPrefix', methods=['get'])
def get_jitter_data_by_prefix():
    prefix = request.args.get('prefix')
    asn = request.args.get('asn')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_data_by_prefix(asn, prefix, st, et, source))


@app.route('/getJitterDataByASNAndPfx', methods=['get'])
def get_jitter_data_by_asn_and_prefix():
    prefix = request.args.get('prefix')
    asn = request.args.get('asn')
    st = request.args.get('st')
    et = request.args.get('et')
    ppfx = request.args.get('ppfx')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_data_by_asn_and_prefix(asn, prefix, ppfx, st, et, source))


@app.route('/getJitterTopPeer', methods=['get'])
def get_jitter_top_n_peer_by_as():
    asn = request.args.get('asn')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_top_n_peer_by_as(asn, st, et, source))


@app.route('/getJitterTopNPeerByPfx', methods=['get'])
def get_jitter_top_n_peer_by_as_and_pfx():
    asn = request.args.get('asn')
    pfx = request.args.get('pfx')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_top_n_peer_by_as_and_pfx(asn, pfx, st, et, source))


@app.route('/getJitterDataByPeerAndPfx', methods=['get'])
def get_jitter_data_by_peer_asn_and_pfx():
    asn = request.args.get('asn')
    pfx = request.args.get('pfx')
    peer = request.args.get('peer')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_data_by_peer_asn_and_pfx(asn, pfx, peer, st, et, source))


@app.route('/getJitterDataByPeer', methods=['get'])
def get_jitter_data_by_peer_asn():
    asn = request.args.get('asn')
    peer = request.args.get('peer')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_data_by_peer_asn(asn, peer, st, et, source))


@app.route('/getJitterPeerASPathByTimeStamp', methods=['get'])
def get_jitter_peer_as_path_by_timestamp():
    asn = request.args.get('asn')
    page_index = request.args.get('page')
    peer = request.args.get('peer')
    time_f = request.args.get('time_f')
    ts = request.args.get('ts')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_peer_as_path_by_timestamp(asn, peer, ts, page_index, time_f, source))


@app.route('/getJitterTopTier1', methods=['get'])
def get_jitter_top_n_tier1_by_as():
    asn = request.args.get('asn')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_top_n_tier1_by_as(asn, st, et, source))


@app.route('/getJitterLastASPathByPrefix', methods=['get'])
def get_jitter_last_as_path_by_prefix():
    asn = request.args.get('asn')
    peer = request.args.get('peer')
    ts = request.args.get('ts')
    prefix = request.args.get('prefix')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_jitter_last_as_path_by_prefix(asn, peer, ts, prefix, source))


@app.route('/getFITIJitterTopNPrefixByPrefix', methods=['get'])
def get_FITI_jitter_topN_prefix_by_prefix():
    prefix = request.args.get('prefix')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_FITI_jitter_topN_prefix_by_prefix(prefix, st, et, source))


@app.route('/getFITIJitterDataByPrefix', methods=['get'])
def get_FITI_jitter_data_by_prefix():
    prefix = request.args.get('prefix')
    p_prefix = request.args.get('p_prefix')
    st = request.args.get('st')
    et = request.args.get('et')
    source = request.args.get('source')
    return jsonify(routing_path_service.get_FITI_jitter_data_by_prefix(p_prefix, prefix, st, et, source))
