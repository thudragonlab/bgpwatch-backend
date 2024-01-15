from typing import Dict

import src.model.home_dao as home_dao
import json
from datetime import datetime
import csv
from io import StringIO
from flask import stream_with_context, Response

from src.service.util import record_last_update_timestamp

with open('static/asn_lat', 'r') as f:
    asn_lat = json.load(f)


# asn_lat = {}
@record_last_update_timestamp
def stats(start, end):
    # home_dao
    try:
        start = int(start) / 1000
        end = int(end) / 1000
    except:
        return {'status': False,
                'message': 'Invalid param'}

    victim_as_list = []
    attacker_as_list = []
    # coords_lines = []
    victim_country_pie_chart = {}
    attacker_country_pie_chart = {}
    prefix_len_histogram = {'v4': {}, 'v6': {}}
    stat_series = []
    event_type_list = [
        {"value": home_dao.get_hijack_count_by_date(start, end, 'Possible Hijack'), "name": "Possible Hijack"},
        {"value": home_dao.get_hijack_count_by_date(start, end, 'Possible SubHijack'), "name": "Possible Subhijack"},
        {"value": home_dao.get_hijack_count_by_date(start, end, 'Ongoing Possible SubHijack'), "name": 'Ongoing Possible SubHijack'},
        {"value": home_dao.get_hijack_count_by_date(start, end, 'Ongoing Possible Hijack'), "name": 'Ongoing Possible Hijack'},
        # {"value": 0, "name": "Route Leak"},
        # {"value": 0, "name": "Outage"},
    ]

    all_series_data_dict = {}

    def get_hijack_list(_type):
        sub_hijack_data = home_dao.projective_hijack_by_date(start, end, _type)
        _sub_hijack_list = []
        for _i in sub_hijack_data:
            _sub_hijack_list.append(_i)
        return _sub_hijack_list

    # hijack_data = home_dao.projective_hijack_by_date(start, end, 'Possible Hijack')
    # hijack_list = []
    # for i in hijack_data:
    #     hijack_list.append(i)

    sub_hijack_list = get_hijack_list('Possible SubHijack')
    hijack_list = get_hijack_list('Possible Hijack')
    ongoing_hijack_list = get_hijack_list('Ongoing Possible Hijack')
    ongoing_subhijack_list = get_hijack_list('Ongoing Possible SubHijack')

    def process_hijack_list(_hijack_list):
        # print(len(_hijack_list))
        for hijack_item in _hijack_list:

            victim_country = 'Unknown' if not hijack_item['before_as_country'] else hijack_item['before_as_country']
            attack_country = 'Unknown' if not hijack_item['suspicious_as_country'] else hijack_item['suspicious_as_country']

            prefix = hijack_item['prefix']
            prefix_num = prefix.split('/')[-1]
            victim_lat = asn_lat[hijack_item['before_as']] if hijack_item['before_as'] in asn_lat else [0, 0]
            attacker_lat = asn_lat[hijack_item['suspicious_as']] if hijack_item['suspicious_as'] in asn_lat else [0, 0]
            # coords_lines.append({'coords':[victim_lat,attacker_lat]})
            victim_as_list.append({
                "country": victim_country,
                "as": hijack_item['before_as'],
                'lon_lat': victim_lat
            })
            # if attack_country == 'CN':
            #     print(prefix,hijack_item['before_as'],hijack_item['suspicious_as'],hijack_item['start_timestamp'])
            attacker_as_list.append({
                "country": attack_country,
                "as": hijack_item['suspicious_as'],
                'lon_lat': attacker_lat
            })

            if victim_country not in victim_country_pie_chart:
                victim_country_pie_chart[victim_country] = 0
            victim_country_pie_chart[victim_country] += 1

            if attack_country not in attacker_country_pie_chart:
                attacker_country_pie_chart[attack_country] = 0
            attacker_country_pie_chart[attack_country] += 1

            if ':' in prefix:
                ip_type = 'v6'
            else:
                ip_type = 'v4'

            if prefix_num not in prefix_len_histogram[ip_type]:
                prefix_len_histogram[ip_type][prefix_num] = 0
            prefix_len_histogram[ip_type][prefix_num] += 1

    process_hijack_list(hijack_list)
    process_hijack_list(sub_hijack_list)
    process_hijack_list(ongoing_hijack_list)
    process_hijack_list(ongoing_subhijack_list)

    single_series_data_dict = {}
    single_series = {'name': 'Possible Hijack'}
    add_in_series(all_series_data_dict, single_series, single_series_data_dict, stat_series, hijack_list)

    single_series_data_dict = {}
    single_series2 = {'name': 'Possible SubHijack'}
    add_in_series(all_series_data_dict, single_series2, single_series_data_dict, stat_series, sub_hijack_list)

    single_series_data_dict = {}
    single_series3 = {'name': 'Onging Possible SubHijack'}
    add_in_series(all_series_data_dict, single_series3, single_series_data_dict, stat_series, ongoing_subhijack_list)

    single_series_data_dict = {}
    single_series4 = {'name': 'Onging Possible Hijack'}
    add_in_series(all_series_data_dict, single_series4, single_series_data_dict, stat_series, ongoing_hijack_list)

    all_series = {'name': 'All', 'data': sorted(list(map(lambda x: [x[0], x[1]], all_series_data_dict.items())),
                                                key=lambda x: x[0])}
    
    max_xAxis_label = []
    for i in sorted(stat_series,key=lambda x:len(x['data']),reverse=True)[0]['data']:
        max_xAxis_label.append(i[0])

    for _stats in stat_series:
        if len(_stats['data']) < len(max_xAxis_label):
            labels = list(map(lambda x:str(x[0]),_stats['data']))
            for label in max_xAxis_label:
                if str(label) not in labels:
                    _stats['data'].append([label,0])

    stat_series = stat_series + [all_series]
    for _stats in stat_series:
        _stats['data'] = sorted(_stats['data'],key=lambda x:x[0])

    return {
        "event_type_pie_chart": event_type_list,
        "victim_as_list": victim_as_list,
        "attacker_as_list": attacker_as_list,
        "victim_country_pie_chart": list(
            map(lambda x: {'name': x[0], 'value': x[1]}, victim_country_pie_chart.items())),
        "attacker_country_pie_chart": list(
            map(lambda x: {'name': x[0], 'value': x[1]}, attacker_country_pie_chart.items())),
        "victim_geo_list": list(map(lambda x: {'name': x}, victim_country_pie_chart.keys())),
        "attacker_geo_list": list(map(lambda x: {'name': x}, attacker_country_pie_chart.keys())),
        "stat_series": stat_series,
        "prefix_len_histogram": prefix_len_histogram,
    }


def add_in_series(all_series_data_dict, single_series2, single_series_data_dict, stat_series, sub_hijack_list):
    for hijack_item in sub_hijack_list:
        start_date = hijack_item['start_timestamp']
        if start_date not in single_series_data_dict:
            single_series_data_dict[start_date] = 0
        single_series_data_dict[start_date] += 1

        if start_date not in all_series_data_dict:
            all_series_data_dict[start_date] = 0
        all_series_data_dict[start_date] += 1
    for i in all_series_data_dict:
        if i not in single_series_data_dict:
            single_series_data_dict[i] = 0
    single_series2['data'] = sorted(list(map(lambda x: [x[0], x[1]], single_series_data_dict.items())),
                                    key=lambda x: x[0])
    # print(len(single_series2['data']))
    stat_series.append(single_series2)


@record_last_update_timestamp
def overview(start, end, cc, asn):
    # print(start, )

    stat_series = []

    hijack_data = home_dao.get_hijack_by_date(start, end, 'Possible Hijack')
    hijack_list = []
    sub_hijack_data = home_dao.get_hijack_by_date(start, end, 'Possible SubHijack')
    sub_hijack_list = []
    if start == -0.001:
        start = 999999999999

    for i in hijack_data:
        start = min(start, i['start_timestamp'] / 1000)
        if cc:
            if i['suspicious_as_country'] == cc or i['before_as_country'] == cc:
                hijack_list.append(i)
        elif asn:
            if i['suspicious_as'] == asn or i['before_as'] == asn:
                hijack_list.append(i)
        else:
            hijack_list.append(i)

    for i in sub_hijack_data:
        if cc:
            if i['suspicious_as_country'] == cc or i['before_as_country'] == cc:
                sub_hijack_list.append(i)
        elif asn:
            if i['suspicious_as'] == asn or i['before_as'] == asn:
                sub_hijack_list.append(i)
        else:
            sub_hijack_list.append(i)

    if len(hijack_list) == 0 and len(sub_hijack_list) == 0:
        return {
            'status': 'failed',
            'statusCode': 'No hijack events!'
        }

    db_map = {'Possible Hijack': hijack_list,
              'Possible SubHijack': sub_hijack_list
              }

    all_series = {'name': 'All', 'data': make_super_series_obj(end, start)}

    for _type in db_map:

        single_series = {'name': _type, 'data': make_super_series_obj(end, start)}

        for hijack_item in db_map[_type]:
            start_date = hijack_item['start_timestamp']
            do = datetime.utcfromtimestamp(start_date / 1000)

            def add_value_in_o(o):
                o['amount'] += 1
                o['min_ts'] = min(o['min_ts'], start_date)
                o['max_ts'] = max(o['max_ts'], start_date)
                if cc:
                    if hijack_item['suspicious_as_country'] == cc:
                        o['attacker_count'] += 1
                    if hijack_item['before_as_country'] == cc:
                        o['victim_count'] += 1
                elif asn:
                    if hijack_item['suspicious_as'] == asn:
                        o['attacker_count'] += 1
                    if hijack_item['before_as'] == asn:
                        o['victim_count'] += 1

            yk = do.year
            mk = f'{do.month}, {do.year}'
            wkey = f'Week {do.isocalendar()[1]}, {do.isocalendar()[0]}'
            k = do.strftime('%Y-%m-%d')

            add_value_in_series(add_value_in_o, k, mk, single_series, start_date, wkey, yk)
            add_value_in_series(add_value_in_o, k, mk, all_series, start_date, wkey, yk)

        stat_series.append(single_series)

    stat_series.append(all_series)
    return {
        "stat_series": stat_series,
    }


def add_value_in_series(add_value_in_o, k, mk, single_series, start_date, wkey, yk):
    # single_series['data'].setdefault(yk, {
    #     'month': {}, 'amount': 0, 'victim_count': 0, 'attacker_count': 0, 'min_ts': start_date,
    #     'max_ts': start_date})
    # single_series['data'][yk]['month'].setdefault(mk, {'weeks': {}, 'amount': 0, 'victim_count': 0,
    #                                                    'attacker_count': 0, 'min_ts': start_date,
    #                                                    'max_ts': start_date})
    single_series['data'][yk]['month'][mk]['weeks'].setdefault(wkey,
                                                               {'days': {}, 'amount': 0, 'victim_count': 0,
                                                                'attacker_count': 0,
                                                                'min_ts': start_date,
                                                                'max_ts': start_date})
    single_series['data'][yk]['month'][mk]['weeks'][wkey]['days'].setdefault(k, {'amount': 0, 'victim_count': 0,
                                                                                 'attacker_count': 0,
                                                                                 'min_ts': start_date,
                                                                                 'max_ts': start_date})
    add_value_in_o(single_series['data'][yk])
    add_value_in_o(single_series['data'][yk]['month'][mk])
    add_value_in_o(single_series['data'][yk]['month'][mk]['weeks'][wkey])
    add_value_in_o(single_series['data'][yk]['month'][mk]['weeks'][wkey]['days'][k])


def make_super_series_obj(end, start) -> Dict:
    day_ts = 60 * 60 * 24
    super_series_obj = {}
    sfd = start
    while sfd <= end:
        do = datetime.utcfromtimestamp(sfd)
        k = do.strftime('%Y-%m-%d')
        month = do.month
        isocalendar = do.isocalendar()
        yk = do.year
        mk = f'{month}, {yk}'
        wkey = f'Week {isocalendar[1]}, {isocalendar[0]}'
        # print(do.isocalendar(), month)
        if yk not in super_series_obj:
            super_series_obj.setdefault(yk, {
                'month': {}, 'amount': 0, 'victim_count': 0, 'attacker_count': 0, 'min_ts': 9999999999999,
                'max_ts': -1})
            # super_series_obj[yk].update(default_obj)
        if mk not in super_series_obj[yk]['month']:
            super_series_obj[yk]['month'].setdefault(mk, {
                'weeks': {}, 'amount': 0, 'victim_count': 0, 'attacker_count': 0, 'min_ts': 9999999999999,
                'max_ts': -1})
            # super_series_obj[yk]['month'][mk].update(default_obj)
        if wkey not in super_series_obj[yk]['month'][mk]['weeks']:
            super_series_obj[yk]['month'][mk]['weeks'].setdefault(wkey, {
                'days': {}, 'amount': 0, 'victim_count': 0, 'attacker_count': 0, 'min_ts': 9999999999999,
                'max_ts': -1})
            # super_series_obj[yk]['month'][mk]['weeks'][wkey].update(default_obj)
        super_series_obj[yk]['month'][mk]['weeks'][wkey]['days'].setdefault(k, {'amount': 0, 'victim_count': 0,
                                                                                'attacker_count': 0,
                                                                                'min_ts': 9999999999999,
                                                                                'max_ts': -1})
        sfd += day_ts
    return super_series_obj


def exportCSV(start, end):
    sd = datetime.utcnow()
    hijack_data = home_dao.get_hijack_event_by_date(start, end, 'Possible Hijack')
    sub_hijack_data = home_dao.get_hijack_event_by_date(start, end, 'Possible SubHijack')
    data = [
        ['EventType', 'Level', 'Event Info', 'Prefix Num', 'Prefix', 'Start Time', 'End Time', 'Duration'],
    ]
    for i in hijack_data:
        _event_type = 'Possible Hijack'
        data.append([_event_type, i['level'],
                     f'Victim:AS{i["victim_as"]} ({i["victim_as_description"]}/{i["victim_as_country"]}){_event_type}:AS{i["hijack_as"]}'
                     f'({i["hijack_as_description"]}/{i["hijack_as_country"]})',
                     len(i['prefix_list']), i['prefix'], i['start_datetime'], i['end_datetime'], i['duration']]),

    for i in sub_hijack_data:
        _event_type = 'Possible SubHijack'
        data.append([_event_type, i['level'],
                     f'Victim:AS{i["victim_as"]} ({i["victim_as_description"]}/{i["victim_as_country"]}){_event_type}:AS{i["hijack_as"]}'
                     f'({i["hijack_as_description"]}/{i["hijack_as_country"]})',
                     len(i['prefix_list']), i['prefix'], i['start_datetime'], i['end_datetime'], i['duration']]),

    # print('FINISH load Data', datetime.utcnow() - sd)

    def generate(_data):
        # 用 StringIO 在内存中写，不会生成实际文件

        io = StringIO()  # 在 io 中写 csv
        w = csv.writer(io)
        for ii in _data:  # 对于 data 中的每一条
            w.writerow(ii)  # 传入的是一个数组 ['xxx','xxx@xxx.xxx'] csv.writer 会把它处理成逗号分隔的一行
            # 需要注意的是传入仅一个字符串 '' 时，会被逐字符分割，所以要写成 ['xxx'] 的形式
            yield io.getvalue()  # 返回写入的值
            io.seek(0)  # io流的指针回到起点
            io.truncate(0)  # 删去指针之后的部分，即清空所有写入的内容，准备下一行的写入
        # 用 generate() 构造返回值

    response = Response(stream_with_context(generate(data)), mimetype='text/csv')
    # 设置Headers: Content-Disposition: attachment 表示默认会直接下载。 指定 filename。
    response.headers.set("Content-Disposition", "attachment",
                         filename=f"{datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')}"
                                  f"-{datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S')}.csv")
    # 将 response 返回
    return response
