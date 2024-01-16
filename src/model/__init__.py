import time

from src import db_config as config
from pymongo import MongoClient
from flask import request
from _datetime import datetime, timezone, timedelta
from src.utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)
conn1 = MongoClient(host=config[1]['host'], port=config[1]['port'], username=config[1]['user'], password=config[1]['pwd'],
                    unicode_decode_error_handler='ignore',
                    maxPoolSize=1024, connect=False)
conn = MongoClient(host=config[0]['host'], port=config[0]['port'], username=config[0]['user'], password=config[0]['pwd'],
                   unicode_decode_error_handler='ignore',
                   maxPoolSize=1024, connect=False)
# server1.close()
user_collection = conn['bgp-user']['user']
user_api_collection = conn['bgp-user']['user_api_log']
transitory_name = 'transitory_name'

utc = timezone(timedelta(hours=0))

last_update_timestamp_map = {}


class MyCollection:
    def __init__(self, db_mapping_name):
        self.mapping_name = db_mapping_name

        self.client = conn
        if 'conn' in collection_name_mapping[db_mapping_name]:
            self.client = collection_name_mapping[db_mapping_name]['conn']

        self.db_name = collection_name_mapping[db_mapping_name]['db_name']
        self.col_name = datetime.utcnow().strftime(collection_name_mapping[db_mapping_name]['col-date_format'])
        self.col = self.client[self.db_name][f'{self.col_name}-{transitory_name}']

    def insert_many(self, *args, **kwargs):
        self.col.insert_many(*args, **kwargs)

    def create_index(self, *args, **kwargs):
        self.col.create_index(*args, **kwargs)

    def finish(self):
        self.col.rename(self.col_name, dropTarget=True)


collection_name_mapping = {
    'dev-daily-as-route': {
        'db_name': 'dev-daily-as-route',
        'collection_name': lambda date: 'as-route-daily-' + date,
        # 'date_format': "%Y%m%d",
        'col-date_format': "as-route-daily-%Y%m%d",
    },
    'serial1': {
        'db_name': 'caida-as-relationships',
        'collection_name': lambda date: date,
        # 'date_format': "%Y%m%d",
        'col-date_format': "%Y%m%d",
    },
    'as_info': {
        'db_name': 'as_info',
        'collection_name': lambda date: date,
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "%Y-%m-%d",
    },
    'cgtf_route_path': {
        'db_name': 'cgtf-route-path',
        'collection_name': lambda date: date,
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "%Y-%m-%d",
    },
    'rtree-hash_info': {
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'prefix-tree-info-{date}',
        # 'date_format': "%Y_%m_%d",
        'col-date_format': "prefix-tree-info-%Y_%m_%d",
        'conn': conn1
    },
    'rtree-tree_info': {
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'tree-hash-{date}',
        # 'date_format': "%Y_%m_%d",
        'col-date_format': "tree-hash-%Y_%m_%d",
        'conn': conn1
    },
    'cluster_info': {
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'cluster-info-{date}',
        # 'date_format': "%Y_%m_%d",
        'col-date_format': "cluster-info-%Y_%m_%d",
        'conn': conn1
    },
    'route_diff_summary': {
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'diff-summary-{date}',
        # 'date_format': "%Y%m%d",
        'col-date_format': "diff-summary-%Y_%m_%d",
        'conn': conn1
    },

    'as-relation': {
        # 'db_name': 'route-as-relationship',
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'as-relationship-{date}',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "as-relationship-%Y_%m_%d",
        'conn': conn1
    },
    'prefix_list': {
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'pfx-name-{date}',
        'col-date_format': "pfx-name-%Y_%m_%d",
        'conn': conn1
    },
    'prefix-count': {
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'prefix-count',
        'col-date_format': "prefix-count",
        'conn': conn1
    },
    'irr_AFRINIC': {
        'db_name': 'irr_whois',
        'collection_name': 'AFRINIC',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "AFRINIC"
    },
    'irr_ARIN': {
        'db_name': 'irr_whois',
        'collection_name': 'ARIN',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "ARIN"
    },
    'irr_RIPE': {
        'db_name': 'irr_whois',
        'collection_name': 'RIPE',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "RIPE"
    },
    'irr_LACNIC': {
        'db_name': 'irr_whois',
        'collection_name': 'LACNIC',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "LACNIC"
    },
    'irr_APNIC': {
        'db_name': 'irr_whois',
        'collection_name': 'APNIC',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "APNIC"
    },
    'irr_WHOIS': {
        'db_name': 'irr_whois',
        'collection_name': 'WHOIS',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "WHOIS-%Y-%m-%d"
    },
    'DOMAIN': {
        'db_name': 'irr_whois',
        'collection_name': 'DOMAIN2',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "DOMAIN2"
    },
    'peer-diff': {
        'db_name': 'peer-diff',
        'collection_name': 'peer-diff',
        # 'date_format': "%Y-%m-%d",
        'col-date_format': "peer-diff"
    },
    'peer-info-specific': {
        'db_name': 'routing_tree_info',
        'collection_name': lambda date: f'peer-info-specific-{date}',
        'col-date_format': "peer-info-specific-%Y_%m_%d",
        'conn': conn1
    },
    'route-jitter': {
        'db_name': 'routing-jitter',
        'collection_name': lambda date: f'routing-jitter-count',
        'col-date_format': "routing-jitter-count",
    },
    'route-jitter-hour': {
        'db_name': 'routing-jitter',
        'collection_name': lambda date: f'routing-jitter-hour',
        'col-date_format': "routing-jitter-hour",
    },
    'route-jitter-peer': {
        'db_name': 'routing-jitter',
        'collection_name': lambda date: f'routing-jitter-peer',
        'col-date_format': "routing-jitter-peer",
    },
    'roa-db': {
        'db_name': 'ROA-DB',
        'collection_name': lambda date: f'roa-db',
        'col-date_format': "roa-db",
    },
    'roa-db-2023': {
        'db_name': 'ROA-DB',
        'collection_name': lambda date: f'roa-db',
        'col-date_format': "roa-db-%Y-%m-%d",
    },
    'test': {
        'db_name': 'test',
        'collection_name': lambda date: f'test',
        'col-date_format': "test",
    }

}

event_collection_map = {
    'Possible Hijack': 'possible-hijack',
    'Moas': 'moas',
    'Ongoing Moas': 'ongoing_moas',
    'SubMoas': 'sub-moas',
    'Ongoing SubMoas': 'ongoing_submoas',
    'Possible SubHijack': 'sub-possible-hijack',
    'Ongoing Possible Hijack': 'ongoing_hijack',
    'Ongoing Possible SubHijack': 'ongoing_subhijack'
}


def get_daily_collection_old(db_mapping_name):
    """
    只找最近一个月的
    """
    existColName = conn[collection_name_mapping[db_mapping_name]['db_name']].collection_names()
    date = datetime.utcnow().strftime(collection_name_mapping[db_mapping_name]['date_format'])
    will_use_collection_name = collection_name_mapping[db_mapping_name]['collection_name'](date)
    if len(existColName) == 0 or (len(existColName) == 1 and existColName[0] == transitory_name):
        will_use_collection_name = collection_name_mapping[db_mapping_name]['collection_name'](date)
    else:
        while will_use_collection_name not in existColName:
            # print(time.strptime(date, collection_name_mapping[db_mapping_name]['date_format']))
            date_stamp = time.mktime(time.strptime(date, collection_name_mapping[db_mapping_name]['date_format']))
            date_stamp -= 24 * 60 * 60
            # if datetime.utcnow().timestamp() - date_stamp > 24 * 60 * 60 * 30:
            #     will_use_collection_name = collection_name_mapping[db_mapping_name]['collection_name'](date)
            #     break
            date = datetime.fromtimestamp(date_stamp).strftime(collection_name_mapping[db_mapping_name]['date_format'])
            will_use_collection_name = collection_name_mapping[db_mapping_name]['collection_name'](date)

    log.debug(f'[Get_daily_collection] will_use_collection_name =====> {will_use_collection_name}')
    return conn[collection_name_mapping[db_mapping_name]['db_name']][will_use_collection_name]


def get_date_of_data(db_mapping_name):
    _table = get_daily_collection(db_mapping_name)
    date = datetime.strptime(_table.name, collection_name_mapping[db_mapping_name]['col-date_format']).strftime('%Y-%m-%d')
    return date

def get_collection_by_timestamp(db_mapping_name,_ts):
    _conn = get_conn_by_name(db_mapping_name)
    will_use_collection_name = datetime.utcfromtimestamp(_ts).strftime(collection_name_mapping[db_mapping_name]['col-date_format'])
    return _conn[collection_name_mapping[db_mapping_name]['db_name']][will_use_collection_name]

def get_daily_collection(db_mapping_name, offset=0):
    """
    只找最近一个月的
    """
    _conn = get_conn_by_name(db_mapping_name)
    existColName = _conn[collection_name_mapping[db_mapping_name]['db_name']].collection_names()
    match_list = []
    for i in existColName:
        try:
            datetime.strptime(i, collection_name_mapping[db_mapping_name]['col-date_format'])
            match_list.append(i)
        except ValueError:
            continue
    match_list.sort(key=lambda x: datetime.strptime(x, collection_name_mapping[db_mapping_name]['col-date_format']).timestamp())
    # log.debug(match_list)
    if len(match_list) != 0:
        if len(match_list) < offset + 1:
            will_use_collection_name = match_list[0]
        else:
            will_use_collection_name = match_list[-(1 + offset)]
    else:
        will_use_collection_name = get_daily_collection_name(db_mapping_name)
    if request:
        last_timestamp = datetime.strptime(will_use_collection_name, collection_name_mapping[db_mapping_name]['col-date_format']).timestamp()
        set_last_update_timestamp_map(last_timestamp)
    return _conn[collection_name_mapping[db_mapping_name]['db_name']][will_use_collection_name]


def set_last_update_timestamp_map(_last_timestamp):
    if request:
        key = f'{request.path}{request.url.split("/", 3)[3]}'
        if key not in last_update_timestamp_map:
            last_update_timestamp_map[key] = _last_timestamp
        else:
            last_update_timestamp_map[key] = max(last_update_timestamp_map[key], _last_timestamp)


def get_conn_by_name(db_mapping_name):
    if 'conn' not in collection_name_mapping[db_mapping_name]:
        return conn
    else:
        return collection_name_mapping[db_mapping_name]['conn']


def get_today_collection(db_mapping_name):
    will_use_collection_name = datetime.utcnow().strftime(collection_name_mapping[db_mapping_name]['col-date_format'])
    # will_use_collection_name = collection_name_mapping[db_mapping_name]['collection_name'](date)
    return conn[collection_name_mapping[db_mapping_name]['db_name']][will_use_collection_name]


def get_daily_collection_name(db_mapping_name):
    will_use_collection_name = datetime.utcnow().strftime(collection_name_mapping[db_mapping_name]['col-date_format'])
    # will_use_collection_name = collection_name_mapping[db_mapping_name]['collection_name'](date)
    return will_use_collection_name


def get_collection(db_name, collection_name):
    return conn[db_name][collection_name]


def get_collection_by_conn1(db_name, collection_name):
    return conn1[db_name][collection_name]


def get_my_collection(db_mapping_name):
    return MyCollection(db_mapping_name)


def init_transitory_daily_collection(db_mapping_name):
    if transitory_name in conn[collection_name_mapping[db_mapping_name]['db_name']].list_collection_names():
        conn[collection_name_mapping[db_mapping_name]['db_name']][transitory_name].drop()
    return conn[collection_name_mapping[db_mapping_name]['db_name']][transitory_name]


def update_transitory_daily_collection_name(db_mapping_name):
    transitory_col = get_transitory_daily_collection(db_mapping_name)
    collection_name = get_daily_collection_name(db_mapping_name)
    if collection_name in conn[collection_name_mapping[db_mapping_name]['db_name']].list_collection_names():
        conn[collection_name_mapping[db_mapping_name]['db_name']][collection_name].drop()
    transitory_col.rename(collection_name)


def get_transitory_daily_collection(db_mapping_name):
    return conn[collection_name_mapping[db_mapping_name]['db_name']][transitory_name]


def get_daily_db(db_mapping_name):
    if 'conn' in collection_name_mapping[db_mapping_name]:
        return collection_name_mapping[db_mapping_name]['conn'][collection_name_mapping[db_mapping_name]['db_name']]
    return conn[collection_name_mapping[db_mapping_name]['db_name']]


def get_info_db():
    date = datetime.now(utc).strftime("%Y-%m-%d")
    return conn['as_info'][date]


def get_col_from_mapping(db_mapping_name):
    db_name = collection_name_mapping[db_mapping_name]['db_name']
    col_name = collection_name_mapping[db_mapping_name]['col-date_format']
    return conn[db_name][col_name]


def get_jitter_table():
    col = get_col_from_mapping('route-jitter')
    col.create_index([('timestamp', -1), ('asn', 1), ('flip', -1)], background=True)
    col.create_index([('expired_date', 1)], background=True, expireAfterSeconds=60 * 60 * 24 * 1)
    col.create_index([('timestamp', 1), ('asn', 1), ('prefix', 1)], background=True)
    return col


def get_jitter_hours_table():
    col = get_col_from_mapping('route-jitter-hour')
    col.create_index([('timestamp', -1), ('asn', 1), ('flip', -1)], background=True)
    col.create_index([('expired_date', 1)], background=True, expireAfterSeconds=60 * 60 * 24 * 14)
    col.create_index([('timestamp', 1), ('asn', 1), ('prefix', 1)], background=True)
    return col


def get_jitter_peer_table():
    col = get_col_from_mapping('route-jitter-peer')
    col.create_index([('expired_date', 1)], background=True, expireAfterSeconds=60 * 60 * 24 * 14)
    return col


def init_roa_db():
    col = get_col_from_mapping('roa-db')
    col.create_index([('binary_prefix', 1), ('timestamp', 1)], background=True)
    col.create_index([('expired_date', 1)], background=True, expireAfterSeconds=60 * 60 * 24 * 7)
    return col


if __name__ == '__main__':
    for k in collection_name_mapping:
        log.debug(k, get_daily_collection(k).name)
