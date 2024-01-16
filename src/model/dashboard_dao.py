from src.model import get_daily_collection, get_collection, get_collection_by_conn1
from src.utils.logger import get_logger, APP_LOG_NAME
log = get_logger(APP_LOG_NAME)
conn1_db = 'routing_tree_info'

def get_prefix_list(asn):
    col = get_daily_collection('prefix_list')
    find_condition = {'_id': asn}
    prefix_item = col.find_one(find_condition)
    return prefix_item


def get_peer_list(asn):
    col = get_daily_collection('as-relation')
    log.debug(col.name)
    find_condition = {'_id': asn}
    peer_list = col.find_one(find_condition)
    return peer_list


def get_route_history_stats(asns):
    col = get_daily_collection('prefix-count')
    # col = get_daily_collection('prefix-count')
    _list = []
    for i in col.find({"_id": {"$in": asns}}):
        _list.append(i)
    return _list


def get_whois_info_by_asn(asn):
    col = get_daily_collection('irr_WHOIS')
    return col.find({'aut-num': f'AS{asn}'})


def get_whois_info_by_org_list(org_list):
    col = get_daily_collection('irr_WHOIS')
    return col.find({'organisation': {'$in':org_list}})

def get_one_whois_info_by_org(org):
    col = get_daily_collection('irr_WHOIS')
    return col.find_one({'organisation': org})

def get_one_whois_info_by_nic(nic):
    col = get_daily_collection('irr_WHOIS')
    return col.find_one({'nic-hdl': nic})


def get_whois_info_by_irt(irt_list):
    col = get_daily_collection('irr_WHOIS')
    return col.find({'irt':{'$in':irt_list}})

def get_one_whois_info_by_irt(irt,source):
    col = get_daily_collection('irr_WHOIS')
    return col.find_one({'irt':irt,'source':source})


def get_whois_info_by_nic(nic_list,source):
    col = get_daily_collection('irr_WHOIS')
    return col.find({'nic-hdl': {'$in': nic_list},'source':source})