import ipaddress
from datetime import datetime
import difflib
from src import app, config
from src.model import user_dao, app_dao, anomaly_dao, subscribe_dao, collection_name_mapping, set_last_update_timestamp_map, get_daily_collection
from src.service.util import parse_token, generate_supernet_regex, generate_subnet_regex, record_last_update_timestamp, get_regex_by_ip
from src.utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)


@record_last_update_timestamp
def add_as_with_list(token, as_list):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    _id = user_info['_id']
    message = 'Subscribe successful'
    status = 'success'
    for key in as_list:
        if not verify_asn_type(key):
            status = 'error'
            break

    if status != 'error':
        if not user_dao.add_as_with_list(_id, as_list, user_info):
            message = 'Subscribe failure'
            status = 'error'
    else:
        message = 'Invalid ASN'

    result = {'message': message,
              'as_list': as_list,
              'status': status
              }
    return result


def verify_asn_type(asn):
    try:
        int(asn)
        return True
    except Exception as e:
        return False


@record_last_update_timestamp
def del_as_in_list(token, as_list):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    _id = user_info['_id']
    as_list = list(map(lambda x: int(x), as_list))
    if user_dao.del_as_in_list(_id, as_list):
        result = {'message': 'Remove subscribed item successful',
                  'as_list': as_list,
                  'status': 'success'
                  }
    else:
        result = {'message': 'Remove subscribed item failure',
                  'as_list': as_list,
                  'status': 'error'
                  }
    return result


@record_last_update_timestamp
def get_subscribed_by_token(token):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    app.logger.info(user_info)
    _id = user_info['_id']
    user_info = user_dao.get_user_subscribe_list(_id)
    changed_as = []
    unchanged_as = []
    _list = []
    if user_info and 'subscribed_as' in user_info.keys():
        as_list = user_info['subscribed_as']
        count = len(as_list)
        subscribed_as = list(map(lambda x: str(x), as_list))
        # print(subscribed_as)
        as_list = app_dao.get_as_diff(subscribed_as)
        for i in as_list:
            if 'summary' in i.keys():
                o = i['summary']
                o['_id'] = i['_id']
                o['to_origin'] = i['to_origin']
                changed_as.append(o)
            else:
                o = i
                unchanged_as.append(o)
            # del
            _list.append(i)

    #     for i in range(math.ceil(count / 30)):
    #         asyncio.run(get_as_diff(subscribed_as[i * 30:(i + 1) * 30], changed_as, unchanged_as))
    changed_as.sort(key=sort_changed_as)
    return {
        'as_list': changed_as + unchanged_as
    }


def sort_changed_as(a):
    return -(a['to_origin_increase'] + a['to_origin_decrease'])


@record_last_update_timestamp
def get_hijack_event(token, st, et):
    result = []
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    _id = user_info['_id']
    user_info = user_dao.get_user_subscribe_list(_id)
    try:
        start_timestamp = int(st) / 1000
        end_timestamp = int(et) / 1000
    except:
        return {'status': False, 'message': 'Invalid param'}

    # now = datetime.now().timestamp()
    # start_ts = now - 86400
    # end_ts = now
    if not user_info or 'subscribed_as' not in user_info:
        return []
    for _event_type in ['Possible Hijack', 'Possible SubHijack', 'Ongoing Possible Hijack', 'Ongoing Possible SubHijack']:
        data = anomaly_dao.find(
            {
                'start_timestamp': {'$gte': int(start_timestamp), '$lte': int(end_timestamp)},
                'victim_as': {'$in': list(map(lambda x: str(x), user_info['subscribed_as']))},
                'duration': {'$not': {'$regex': '-'}}}, _event_type)
        if 'Possible Hijack' in _event_type:
            if 'Ongoing' in _event_type:
                for i in data:
                    o = {
                        '_id': i['_id'].__str__(),
                        'event_id': i['event_id'],
                        'Description': f'Victim:{i["victim_as_country"]}/AS{i["victim_as"]}({i["victim_as_description"]})<br> Attacker:{i["hijack_as_country"]}/AS{i["hijack_as"]}({i["hijack_as_description"]})',
                        'event_type': _event_type, 'prefix_num': 1,
                        'victim': i['victim_as'],
                        'attacker': i['hijack_as'],
                        'example_prefix': i['prefix'], 'level': i['level'],
                        'level_reason': i['level_reason'], 'start_time': i['start_datetime'], 'end_time': '-',
                        'duration': '-',
                        'detail_url': '/events/%s|%s' % (i['event_id'].replace('/', '_'), _event_type),
                        'confirm': i['confirm'] if 'confirm' in i else [],
                        'reject': list(i['reject'].keys()) if 'reject' in i else [],
                        'logging': i['logging'] if 'logging' in i else []
                    }
                    # ObjectId()
                    result.append(o)
            else:
                for i in data:
                    # if '-' in i['duration']:
                    #     i['duration'] = '-'
                    # print(i['logging'] if 'logging' in i else [])
                    o = {
                        '_id': i['_id'].__str__(),
                        'event_id': i['event_id'],
                        'Description': f'Victim:{i["victim_as_country"]}/AS{i["victim_as"]}({i["victim_as_description"]})<br> Attacker:{i["hijack_as_country"]}/AS{i["hijack_as"]}({i["hijack_as_description"]})',
                        'event_type': _event_type, 'prefix_num': len(i['prefix_list']),
                        'victim': i['victim_as'],
                        'attacker': i['hijack_as'],
                        'example_prefix': i['prefix_list'][0], 'level': i['level'],
                        'level_reason': i['level_reason'], 'start_time': i['start_datetime'],
                        'end_time': i['end_datetime'],
                        'duration': i['duration'],
                        'prefix_list': i['prefix_list'],
                        'detail_url': '/events/%s|%s' % (i['event_id'].replace('/', '_'), _event_type),
                        'confirm': i['confirm'] if 'confirm' in i else [],
                        'reject': list(i['reject'].keys()) if 'reject' in i else [],
                        'logging': i['logging'] if 'logging' in i else []
                    }
                    # ObjectId()
                    result.append(o)
        elif 'Possible SubHijack' in _event_type:
            if 'Ongoing' in _event_type:
                for i in data:
                    o = {
                        '_id': i['_id'].__str__(),
                        'event_id': i['event_id'],
                        'Description': f'Victim:{i["victim_as_country"]}/AS{i["victim_as"]}({i["victim_as_description"]})<br> Attacker:{i["hijack_as_country"]}/AS{i["hijack_as"]}({i["hijack_as_description"]})',
                        'event_type': _event_type, 'prefix_num': 1,
                        'victim': i['victim_as'],
                        'attacker': i['hijack_as'],
                        'example_prefix': f'''<div>prefix: </div> <div>{i['prefix']}</div><div>subprefix: </div> <div>{i['subprefix']}</div>''',
                        'level': i['level'],
                        'level_reason': i['level_reason'], 'start_time': i['start_datetime'], 'end_time': '-',
                        'duration': '-',
                        'prefix_list': [[i['prefix'], i['subprefix']]],
                        'detail_url': '/events/%s|%s' % (i['event_id'].replace('/', '_'), _event_type),
                        'confirm': i['confirm'] if 'confirm' in i else [],
                        'reject': list(i['reject'].keys()) if 'reject' in i else [],
                        'logging': i['logging'] if 'logging' in i else []
                    }

                    # ObjectId()
                    result.append(o)
            else:
                for i in data:
                    if '-' in i['duration']:
                        i['duration'] = '-'
                    o = {
                        '_id': i['_id'].__str__(),
                        'event_id': i['event_id'],
                        'Description': f'Victim:{i["victim_as_country"]}/AS{i["victim_as"]}({i["victim_as_description"]})<br> Attacker:{i["hijack_as_country"]}/AS{i["hijack_as"]}({i["hijack_as_description"]})',
                        'event_type': _event_type, 'prefix_num': len(i['prefix_list']),
                        'example_prefix': f'''<div>prefix: </div> <div>{i['prefix']}</div><div>subprefix: </div> <div>{i['subprefix']}</div>''',
                        'level': i['level'],
                        'victim': i['victim_as'],
                        'attacker': i['hijack_as'],
                        'level_reason': i['level_reason'], 'start_time': i['start_datetime'],
                        'end_time': i['end_datetime'],
                        'duration': i['duration'],
                        'prefix_list': i['prefix_list'],
                        'detail_url': '/events/%s|%s' % (i['event_id'].replace('/', '_'), _event_type),
                        'confirm': i['confirm'] if 'confirm' in i else [],
                        'reject': list(i['reject'].keys()) if 'reject' in i else [],
                        'logging': i['logging'] if 'logging' in i else []
                    }

                    # ObjectId()
                    result.append(o)

    return result


@record_last_update_timestamp
def confirm_event(_id, event_type, token, description='-'):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    print(user_info)
    update_count = anomaly_dao.update_confirm(_id, user_info['_id'], user_info['username'], event_type, description)
    if update_count == 1:
        return {'status': True}
    else:
        return {'status': False, 'msg': 'Not Found event'}


@record_last_update_timestamp
def reject_event(_id, event_type, reason, token):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    update_count = anomaly_dao.update_reject(_id, user_info['_id'], user_info['username'], reason, event_type)
    if update_count == 1:
        return {'status': True}
    else:
        return {'status': False, 'msg': 'Not Found event'}


@record_last_update_timestamp
def unconfirmed_event(_id, event_type, token):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    update_count = anomaly_dao.update_unconfirmed(_id, user_info['_id'], event_type)
    if update_count == 1:
        return {'status': True}
    else:
        return {'status': False, 'msg': 'Not Found event'}


@record_last_update_timestamp
def un_reject_event(_id, event_type, token):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    update_count = anomaly_dao.un_reject_event(_id, user_info['_id'], event_type)
    if update_count == 1:
        return {'status': True}
    else:
        return {'status': False, 'msg': 'Not Found event'}


@record_last_update_timestamp
def get_peer_diff(token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    user_info = user_dao.get_user_subscribe_list(_id)
    result = []
    if user_info and 'subscribed_as' in user_info:
        db_result = subscribe_dao.get_peer_diff(list(map(lambda x: str(x), user_info['subscribed_as'])))
        for i in db_result:
            o = {}
            o['_id'] = i['_id']
            o['diff'] = {'+': list(map(lambda x: x[2:], filter(lambda x: x[0] == '+', i['diff']))),
                         '-': list(map(lambda x: x[2:], filter(lambda x: x[0] == '-', i['diff']))), 'status': len(i['diff']) != 0}
            o['set'] = i['peers']
            result.append(o)
    return result


@record_last_update_timestamp
def add_sub_comment(_id, event_type, comment, parent_user_id, token, reply_user=''):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    update_count, comment_id = anomaly_dao.add_sub_comment(_id, parent_user_id, user_info, event_type, comment, reply_user)
    if update_count == 1:
        return {'status': True, 'comment_id': comment_id}
    else:
        return {'status': False, 'msg': 'Not Found event'}


@record_last_update_timestamp
def del_sub_comment(_id, event_type, comment_id, parent_user_id, token):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    update_count = anomaly_dao.del_sub_comment(_id, parent_user_id, event_type, comment_id)
    if update_count == 1:
        return {'status': True, 'comment_id': comment_id}
    else:
        return {'status': False, 'msg': 'Not Found event'}


@record_last_update_timestamp
def get_peer_stats(token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    user_info = user_dao.get_user_subscribe_list(_id)
    result = []
    if user_info and 'subscribed_as' in user_info:
        db_result = subscribe_dao.get_peer_stats(list(map(lambda x: str(x), user_info['subscribed_as'])))
        for i in db_result:
            i['peer_num'] = list(map(lambda x: ["".join(x[0].split("_")), x[1]], list(i['peer_num'].items())[-30:]))
            result.append(i)
    return result


@record_last_update_timestamp
def search_as2prefix_path(token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    final_result = {}
    user_info = user_dao.get_user_subscribed_as_prefix(_id)
    if user_info and 'subscribed_as_prefix' in user_info:
        for asn in user_info['subscribed_as_prefix']:
            final_result[asn] = {}
            for prefix in user_info['subscribed_as_prefix'][asn]:
                print(asn, prefix)
                final_result[asn][prefix] = process_asn_and_prefix(asn, prefix)

    return final_result
    # return {}


def process_asn_and_prefix(_asn, prefix):
    dur = 7
    org_prefix = prefix
    prefix_list = prefix.split('/')
    if len(prefix_list) == 1:
        if ':' in prefix:
            prefix_list.append('128')
            prefix = f'{prefix}/128'
        else:
            prefix_list.append('32')
            prefix = f'{prefix}/32'
    if ':' in prefix:
        prefix_list[0] = ipaddress.ip_address(prefix_list[0]).exploded
        prefix = '/'.join(prefix_list)
    # condition = {
    #     '_id': prefix
    # }
    condition = {
        '$or': [],
        '$and': [{'Hash': {'$ne': '-1'}}, {'Hash': {'$ne': -1}}],
    }
    condition['$or'].append({'binary': {'$regex': f'{generate_subnet_regex(prefix)}'}})
    condition['$or'].append({'_id': {'$in': generate_supernet_regex(prefix)}})

    def get_daily_tree_data(prefix_col_name, tree_col_name):
        hash_info_list = subscribe_dao.get_one_route_by_condition(prefix_col_name, condition)
        inner_result = {'status': False, 'msg': f'Not found prefix {org_prefix}', 'path': [], 'prefix': prefix}
        if hash_info_list.count() == 0:
            return inner_result

        # hash_info = sorted(list(hash_info_list), key=lambda x: abs(int(x['_id'].split('/')[-1]) - int(prefix_list[1])))[0]
        for hash_info in hash_info_list:
            print(hash_info['_id'])
            # if not hash_info:
            #     return {'status': False, 'msg': f'Not found prefix {org_prefix}', 'path': []}
            _hash = hash_info['Hash']
            rtree_info = subscribe_dao.get_rtree_by_hash(tree_col_name, _hash)
            if not rtree_info:
                inner_result = {'status': False, 'msg': f'Not found prefix {org_prefix}', 'path': [], 'prefix': prefix}
                continue

            edge = rtree_info['edges']

            nodes = [item for sublist in list(edge.values()) for item in sublist] + rtree_info['Allroots']
            print(nodes)
            if _asn not in nodes:

                inner_result = {'status': False, 'msg': f'ASN {_asn} not match prefix routing tree', 'path': [], 'prefix': prefix}
                continue
            root = rtree_info['ASroots'][0]
            reverse_as_path = {}

            for e in edge:
                for n in edge[e]:
                    if n not in reverse_as_path:
                        reverse_as_path[n] = []
                    if n == e:
                        continue
                    reverse_as_path[n].append(e)

            path_dict = []

            def get_path(_path, source_asn):
                # print(reverse_as_path)
                for new_source_asn in reverse_as_path[source_asn]:
                    _path.append(new_source_asn)
                    if new_source_asn == root:
                        path_dict.append(_path)
                        break
                    get_path(_path, new_source_asn)

            if _asn == root:
                shortest_path = [f'{root}|0']
            else:
                get_path([_asn], _asn)

                # for pp in path_dict:
                #     print(pp)
                shortest_path = min(path_dict, key=lambda x: len(x))
                shortest_path = [f'{_as}|{index}' for index, _as in enumerate(shortest_path)]
                # print(shortest_path)
            inner_result = {'status': True, 'msg': '', 'path': shortest_path, 'prefix': hash_info['_id']}
            break
        return inner_result

    final_result = {}
    set_last_update_timestamp_map(datetime.now().timestamp())

    last_key = ''

    for i in range(dur - 1, -1, -1):
        # print(i)
        prefix_tree_info_col_name = get_daily_collection('rtree-hash_info', i).name
        tree_info_col_name = get_daily_collection('rtree-tree_info', i).name

        date_key = datetime.strptime(prefix_tree_info_col_name, collection_name_mapping['rtree-hash_info']['col-date_format']).strftime('%Y-%m-%d')
        result = get_daily_tree_data(prefix_tree_info_col_name, tree_info_col_name)

        final_result[date_key] = result

        if last_key == '':
            last_key = date_key
            print(date_key)
            continue
        old_path = final_result[last_key]
        diff = difflib.ndiff(old_path['path'], result['path'])
        print(old_path['path'])
        print(result['path'])
        final_result[date_key]['diff'] = []
        for iii in diff:
            print(iii)
            if '?' in iii:
                continue
            if '-' in iii or '+' in iii:
                final_result[date_key]['diff'].append(iii)
        last_key = date_key
    return final_result


@record_last_update_timestamp
def add_prefix_subscribe(asn, prefix, token):
    auth = token.split(' ')
    user_info = parse_token(auth[1])
    _id = user_info['_id']

    prefix_list = prefix.split('/')

    if len(prefix_list) == 1:
        if ':' in prefix:
            prefix_list.append('128')
            prefix = f'{prefix}/128'
        else:
            prefix_list.append('32')
            prefix = f'{prefix}/32'

    if ':' in prefix:
        prefix_list[0] = ipaddress.ip_address(prefix_list[0]).exploded
        prefix = '/'.join(prefix_list)

    if user_dao.add_prefix_subscribe(_id, asn, prefix):
        return {'status': True, 'msg': 'Success'}
    else:
        return {'status': False, 'msg': 'Not found User'}


@record_last_update_timestamp
def search_as2prefix_path_info(token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    final_result = {}
    user_info = user_dao.get_user_subscribed_as_prefix(_id)
    if user_info and 'subscribed_as_prefix' in user_info:
        for asn in user_info['subscribed_as_prefix']:
            final_result[asn] = {}
            for prefix in user_info['subscribed_as_prefix'][asn]:
                final_result[asn][prefix] = []

    return final_result


@record_last_update_timestamp
def get_as2prefix_path(asn, prefix):
    result = process_asn_and_prefix(asn, prefix)
    return result


@record_last_update_timestamp
def remove_as2prefix_path(asn, prefix, token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    user_info = user_dao.get_user_subscribed_as_prefix(_id)
    print(_id, asn, prefix, user_info['subscribed_as_prefix'])
    if user_info and 'subscribed_as_prefix' in user_info and asn in user_info['subscribed_as_prefix']:
        if len(user_info['subscribed_as_prefix'][asn]) > 1:
            if user_dao.del_prefix_in_prefix_list(_id, asn, prefix):
                return {'status': True, 'msg': 'Success'}
        else:
            if user_dao.del_asn_in_prefix_list(_id, asn):
                return {'status': True, 'msg': 'Success'}
    return {'status': False, 'msg': 'Not found User'}
