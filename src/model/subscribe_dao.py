from src.model import *
from src.utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)
PEER_DIFF = 'peer-info-specific'
CONN1_DB = 'routing_tree_info'
PEER_INFO = 'peer-info'


def get_peer_diff(as_list):
    col = get_daily_collection(PEER_DIFF)
    condition = {'_id': {'$in': as_list}}
    result = col.find(condition)
    return result


def get_peer_stats(as_list):
    col = get_collection_by_conn1(CONN1_DB, PEER_INFO)
    condition = {'_id': {'$in': as_list}}
    result = col.find(condition)
    return result


def get_one_route_by_condition(col_name, condition):
    col = get_collection_by_conn1(CONN1_DB, col_name)
    return col.find(condition)


def get_rtree_by_hash(col_name, _hash):
    col = get_collection_by_conn1(CONN1_DB, col_name)
    try:
        rtree_info = col.find_one({'_id': int(_hash)})
    except Exception as e:
        log.error(e)
        rtree_info = col.find_one({'_id': _hash})
    return rtree_info
