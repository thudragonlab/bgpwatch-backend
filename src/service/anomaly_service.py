import os

import src.model.anomaly_dao as anomaly_dao
from datetime import datetime
import threading
from src.service.app_service import get_as_info_by_list_service
from src.service.util import record_last_update_timestamp, ip_to_ipbinary
from utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)

event_type_list = ['Possible Hijack', 'Possible SubHijack', 'Ongoing Possible Hijack', 'Ongoing Possible SubHijack']
moas_event_type_list = ['Moas', 'SubMoas','Ongoing Moas','Ongoing SubMoas']


@record_last_update_timestamp
def events(st, et, event_type):
    result = []
    # Param was UTC+8 time str
    # d = pytz.timezone('Asia/Shanghai')
    # Transform param to timestamp
    # start_timestamp = d.localize(datetime.strptime(st, "%Y-%m-%d %H:%M:%S")).timestamp()
    # end_timestamp = d.localize(datetime.strptime(et, "%Y-%m-%d %H:%M:%S")).timestamp()
    try:
        start_timestamp = int(st) / 1000
        end_timestamp = int(et) / 1000
    except:
        return {'status': False, 'message': 'Invalid param'}
    # start_timestamp = datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()
    # end_timestamp = datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()

    log.debug(f'{start_timestamp},{end_timestamp}')
    total = 0
    limit = False
    MAX_LIMIT = 20000
    def make_data(_event_type):
        nonlocal total
        nonlocal limit
        data = anomaly_dao.get_events(start_timestamp, end_timestamp, _event_type)

        for i in data:
            total += 1
            if total > MAX_LIMIT:
                limit = True
                break
            if 'Hijack' in _event_type:
                o = {
                    'Description': f'Victim:{i["victim_as_country"]}/AS{i["victim_as"]}({i["victim_as_description"]})<br> Attacker:{i["hijack_as_country"]}/AS{i["hijack_as"]}({i["hijack_as_description"]})',
                    'event_type': _event_type, 'prefix_num': 1,
                    'victim': i['victim_as'],
                    'attacker': i['hijack_as'],
                    'example_prefix': i['prefix'],
                    'level': i['level'],
                    # 'level_reason': i['level_reason'] if len(i['websites']) == 0 else f"{len(i['websites'])} websites in the prefix.",
                    'start_time': i['start_datetime'], 'end_time': '-',
                    'duration': '-',
                    # 'prefix_list': i['prefix_list'],
                    'detail_url': '/events/%s|%s' % (i['event_id'].replace('/', '_'), _event_type)}
                # ObjectId()
                if 'Ongoing Possible SubHijack' in _event_type:
                    o['example_prefix'] = f'''<div>prefix: </div> <div>{i['prefix']}</div><div>subprefix: </div> <div>{i['subprefix']}</div>'''
                    o['prefix_list'] = [[i['prefix'], i['subprefix']]]
                    if 'websites_in_prefix' in i:
                        i['websites'] = i['websites_in_prefix']
                    i['websites'] = list(set([item for sublist in list(i['websites'].values()) for item in sublist]))
                elif 'Possible SubHijack' in _event_type:
                    o['example_prefix'] = f'''<div>prefix: </div> <div>{i['prefix']}</div><div>subprefix: </div> <div>{i['subprefix']}</div>'''
                    if 'prefix_list' in i:
                        o['prefix_list'] = i['prefix_list']
                        o['prefix_num'] = len(o['prefix_list'])
                    else:
                        o['prefix_list'] = [[i['prefix'], i['subprefix']]]
                    o['duration'] = i['duration']
                    o['end_time'] = i['end_datetime']
                    if 'websites_in_prefix' in i:
                        i['websites'] = i['websites_in_prefix']
                    i['websites'] = list(set([item for sublist in list(i['websites'].values()) for item in sublist]))
                elif 'Ongoing Possible Hijack' in _event_type:
                    if 'websites_in_prefix' in i:
                        i['websites'] = list(set(i['websites_in_prefix']))
                elif 'Possible Hijack' in _event_type:
                    if 'websites_in_prefix' in i:
                        i['websites'] = i['websites_in_prefix']
                    i['websites'] = list(set([item for sublist in list(i['websites'].values()) for item in sublist]))
                    o['prefix_list'] = i['prefix_list']
                    o['prefix_num'] = len(i['prefix_list'])
                    o['duration'] = i['duration']
                    o['end_time'] = i['end_datetime']

                o['level_reason'] = i['level_reason'] if len(i['websites']) == 0 else f"{len(i['websites'])} websites in the prefix."
                # print(o['level_reason'])
                result.append(o)
            elif 'Moas' in _event_type:
                o = {
                    'Description': f'Before:{i["before_as_country"]}/AS{i["before_as"]}({i["before_as_description"]})<br> Suspicious:{i["suspicious_as_country"]}/AS{i["suspicious_as"]}({i["suspicious_as_description"]})',
                    'event_type': _event_type, 'prefix_num': 1, 'victim': i['before_as'], 'attacker': i['suspicious_as'],
                    'example_prefix': i['prefix'], 'level': i['level'], 'start_time': i['start_datetime'], 'end_time': '-', 'duration': '-',
                    'detail_url': '/events/%s|%s' % (i['event_id'].replace('/', '_'), _event_type)
                    # 'level_reason': i['level_reason'] if len(i['websites']) == 0 else f"{len(i['websites'])} websites in the prefix."
                }
                # print(o['level_reason'])
                if 'Moas' == _event_type:
                    i['websites'] = list(set([item for sublist in list(i['websites'].values()) for item in sublist]))
                    o['prefix_list'] = i['prefix_list']
                    o['prefix_num'] = len(i['prefix_list'])
                    o['duration'] = i['duration']
                    o['end_time'] = i['end_datetime']
                elif 'Ongoing Moas' == _event_type:
                    if 'websites_in_prefix' in i:
                        i['websites'] = list(set(i['websites_in_prefix']))
                elif 'SubMoas' == _event_type:
                    o['duration'] = i['duration']
                    o['end_time'] = i['end_datetime']
                    if 'prefix_list' in i:
                        o['prefix_list'] = i['prefix_list']
                    else:
                        o['prefix_list'] = [[i['prefix'], i['subprefix']]]
                    o['prefix_num'] = len(i['prefix_list'])
                    if 'websites_in_prefix' in i:
                        i['websites'] = i['websites_in_prefix']
                    o['example_prefix'] = f'''<div>prefix: </div> <div>{i['prefix']}</div><div>subprefix: </div> <div>{i['subprefix']}</div>'''
                    i['websites'] = list(set([item for sublist in list(i['websites'].values()) for item in sublist]))
                elif 'Ongoing SubMoas' == _event_type:
                    o['example_prefix'] = f'''<div>prefix: </div> <div>{i['prefix']}</div><div>subprefix: </div> <div>{i['subprefix']}</div>'''
                    o['prefix_list'] = [[i['prefix'], i['subprefix']]]
                    if 'websites_in_prefix' in i:
                        i['websites'] = i['websites_in_prefix']
                    i['websites'] = list(set([item for sublist in list(i['websites'].values()) for item in sublist]))
                o['level_reason'] = i['level_reason'] if len(i['websites']) == 0 else f"{len(i['websites'])} websites in the prefix."
                result.append(o)

    if event_type == 'ALL':
        for e_t in event_type_list:
            if total > MAX_LIMIT:
                limit = True
                break
            make_data(e_t)
    elif event_type == 'ALL_MOAS':
        for e_t in moas_event_type_list:
            if total > MAX_LIMIT:
                limit = True
                break
            make_data(e_t)
    else:
        make_data(event_type)
    return {
        'data': result,
        'limit': limit
    }


@record_last_update_timestamp
def get_event_detail(event_param):
    event_param_list = event_param.split('|')
    log.debug(f"{event_param_list}")
    if len(event_param_list) == 1:
        return {'status': False, 'message': 'Invaild param'}

    data,_type = anomaly_dao.get_event_detail(event_param)
    data['_id'] = data['_id'].__str__()
    if _type:
        data['event_type'] = _type
    else:
        data['event_type'] = event_param_list[1]
    data['victim_as'] = data['before_as']
    data['victim_as_description'] = data['before_as_description']
    if data['before_as_country']:
        data['victim_as_country'] = data['before_as_country']
    data['hijacker_as'] = data['suspicious_as']
    data['hijacker_as_description'] = data['suspicious_as_description']
    if data['suspicious_as_country']:
        data['hijacker_as_country'] = data['suspicious_as_country']

    data['start_time'] = data['start_datetime']

    # del data['end_time']

    if 'end_datetime' in data:
        data['end_time'] = data['end_datetime']

    if 'websites_in_prefix' in data:
        data['websites'] = data['websites_in_prefix']

    if 'prefix_list' not in data:
        data['prefix_list'] = [data['prefix']]
        if 'subprefix' in data:
            data['prefix_list'].append(data['subprefix'])
    # del data['_id']
    if 'Sub' in data['event_type']:

        data['websites'] = [item.strip('}\'\'{') for sublist in data['websites'].values() for item in sublist]
        if 'replay' in data:
            as_set = set()
            for i in data['replay']:
                for as_path_list in data['replay'][i].values():
                    if as_path_list == []:
                        continue

                    for as_path in as_path_list:
                        if '{' in as_path or '}' in as_path:
                            continue
                        as_set = as_set.union(list(map(lambda x: int(x), as_path.split(' '))))
            data['affacted_as_dict'] = get_as_info_by_list_service(list(as_set))['data']
    else:
        if 'Ongoing' in data['event_type']:
            if data['websites']:
                data['websites'] = [item for sublist in list(
                    map(lambda x: x.strip('}\'\'{').split('\', \'') if len(x) else [], data['websites'])) for item
                                    in sublist]

        else:

            data['websites'] = [item for sublist in list(data['websites'].values()) for item in sublist]
            # print(data['websites'])

        if 'replay' in data:
            as_set = set()

            for i in data['replay']:

                for as_path in data['replay'][i]['path_list']:
                    if '{' in as_path or '}' in as_path:
                        continue
                    for _as in as_path.split(' '):
                        as_set.add(int(_as))
            data['affacted_as_dict'] = get_as_info_by_list_service(list(as_set))['data']
    data['websites'] = list(set(data['websites']))
    return data


def domain_finish():
    def run():
        os.system('bash domain.sh')

    th = threading.Thread(target=run, name="thread_1")
    th.start()
    return {'msg': 'run domain.sh!'}


def get_event_by_condition(hijack_type, condition):
    result = anomaly_dao.get_events_by_condition(hijack_type, condition)
    _list = []
    ban_list = ['confirm', 'reject', 'replay', 'before_as', 'before_as_country', 'before_as_description', 'suspicious_as', 'suspicious_as_country',
                'suspicious_as_description', 'is_subhijack', 'is_hijack', 'hash_0', 'moas_set', 'after_as', 'reason', 'lg_result', 'prefix',
                'event_info']
    for i in result:
        i['event_id'] = i['_id'].__str__()
        del i['_id']
        i['type'] = hijack_type
        for attr in ban_list:
            if attr in i:
                del i[attr]
        _list.append(i)
    return _list


def get_event_detail_by_api(hijack_type, event_id):
    # ban_list = ['_id', 'confirm', 'reject', 'before_as', 'before_as_country', 'before_as_description', 'suspicious_as',
    #             'suspicious_as_country',
    #             'suspicious_as_description', 'is_subhijack', 'is_hijack', 'hash_0', 'moas_set','after_as','lg_result','prefix','event_info']
    result = anomaly_dao.get_event_detail_by_api(hijack_type, event_id)

    for i in result['replay']:
        for ii in result['replay'][i].copy():
            if ii in ['community', 'stat']:
                del result['replay'][i][ii]
    # for attr in ban_list:
    #     if attr in result:
    #         del result[attr]
    return result['replay']

@record_last_update_timestamp
def get_prefix_roa_history(prefix):
    binary_prefix = ip_to_ipbinary(prefix)
    bin_prefix_len = len(binary_prefix)
    binary_prefix_list = [binary_prefix[:ii] for ii in range(bin_prefix_len, 0, -1)]
    data = anomaly_dao.get_prefix_roa_history(binary_prefix_list)
    result = {}
    for i in data:
        prefix = i['prefix']
        if prefix not in result:
            result[prefix] = []
        result[prefix].append({
            'asn_list':i['asn'],
            'timestamp':i['timestamp']
        })
    return result
