import ipaddress

import src.model.app_dao as app_dao
import json
import re

from src.service.routing_path_service import aggregate_point_relation, recursive_for_point_relation
from src import app
from typing import Dict, List
import math
import os
import aiohttp
import numpy
import base64
import requests

from src.model import user_dao, app_dao, routing_path_dao, dashboard_dao
from src.service.draw_rtree import draw_rtree, draw_graph_by_prefix, LinkType
from src.service.util import parse_token, generate_supernet_regex, generate_subnet_regex, record_last_update_timestamp, get_regex_by_ip
from src.utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)
typeMap = {
    'provider': 'provider-ases',
    'customer': 'customer-ases',
    'peer': 'peer-ases'
}

GET_AS_DIFF_API = 'http://10.110.62.37:5050/api/route_diff_summary'


@record_last_update_timestamp
def get_providers_service(asn, col_type):
    links = []
    sub_link = []
    tier1_list = []
    point_relation = {}
    result = []
    final_hop = 5
    if col_type == 'peer':
        final_hop = 2
    elif col_type == 'customer':
        final_hop = 2
    get_layer_by_as([asn], links, tier1_list, point_relation, typeMap[col_type], final_hop, sub_link)
    log.debug(f'{point_relation}')
    handle_point_relation(asn, point_relation)
    # print(point_relation)
    if point_relation:
        result = point_relation[asn]

    return {
        'link': links,
        # 'sub_link': sub_link,
        # 'data': data,
        'tier1List': tier1_list,
        'result': result
        # 'link': [],
        # 'data': [],
    }


def get_layer_by_as(asn_list, links, tier1_list, point_relation, column_name, final_hop, sub_link, pass_point=None,
                    times=1):
    if pass_point is None:
        pass_point = []
    if times == final_hop:
        return
    array1 = []
    for key in asn_list:
        point = app_dao.find_by_key_from_mongo(key)
        if not point:
            continue
        providers = list(set(point[column_name]))
        providers.sort()

        point_relation[key] = {}
        point_relation[key]['width'] = 1
        # 如果当前key是tier1
        if not len(providers):
            tier1_list.append(key)
            # point_relation[key]['width'] += 1
        for provider_as in providers:
            if provider_as not in pass_point:
                pass_point.append(provider_as)
                array1.append(provider_as)

                point_relation[key][provider_as] = {}
                # 如果在递归边界，比如递归5次，子节点在第5次上，外面不会记录子节点
                point_relation[provider_as] = {}
                point_relation[provider_as]['width'] = 1

                links.append({
                    'source': key,
                    'target': provider_as
                })
            else:
                sub_link.append({
                    'source': key,
                    'target': provider_as
                })

    if len(array1) == 0:
        return
    else:
        get_layer_by_as(array1, links, tier1_list, point_relation, column_name, final_hop, sub_link, pass_point,
                        times + 1)


def handle_point_relation(asn, point_relation):
    if not point_relation:
        return point_relation
    if len(point_relation[asn].keys()) == 1:
        return point_relation[asn]

    for key in point_relation[asn].keys():
        if key in point_relation.keys():
            if key == 'width':
                continue
            temp = handle_point_relation(key, point_relation)
            point_relation[asn][key].update(temp)
            point_relation[asn]['width'] += temp['width']
    point_relation[asn]['width'] -= 1
    return point_relation[asn]


def handle_providers_4538_data(path, point_relation, links, pass_point):
    for index, point in enumerate(path[1:6]):
        source = '4538'
        if '{' in point:
            continue
        if point not in pass_point:
            # print(point)
            pass_point.append(point)
            if index != 0:
                source = path[1:6][index - 1]
            if source not in point_relation.keys():
                point_relation[source] = {'width': 1}
            point_relation[source][point] = {}
            point_relation[point] = {'width': 1}
            links.append({
                'source': source,
                'target': point
            })
    return 1


@record_last_update_timestamp
def get_peer_type_distribute_service(asn):
    country_distribute = []
    customer_list = []
    provider_list = []
    peer_list = []
    peer_type_list = []

    asn_info = app_dao.find_by_key_from_mongo(asn)

    if asn_info:
        customer_prefixes = app_dao.get_prefixes_in_as_list(asn_info['customer-ases'])
        provider_prefixes = app_dao.get_prefixes_in_as_list(asn_info['provider-ases'])
        peer_prefixes = app_dao.get_prefixes_in_as_list(asn_info['peer-ases'])

        format_list(customer_list, customer_prefixes, asn_info['customer-ases'])
        format_list(provider_list, provider_prefixes, asn_info['provider-ases'])
        format_list(peer_list, peer_prefixes, asn_info['peer-ases'])

        peer_type_list.append({'name': 'C-P', 'value': asn_info['customer-ases-count']})
        peer_type_list.append({'name': 'P-C', 'value': asn_info['provider-ases-count']})
        peer_type_list.append({'name': 'P-P', 'value': asn_info['peer-ases-count']})

        array = list(set(asn_info['customer-ases'] + asn_info['provider-ases'] + asn_info['peer-ases']))
        b = app_dao.get_country_distribute(list(map(lambda x: int(x), array)))
        for i in b:
            country_distribute.append({'name': i['_id'], 'value': i['sum']})

        for customer in customer_prefixes:
            customer_list.append({
                'name': customer['_id'],
                'prefixes': customer['prefixes']
            })

        for provider in provider_prefixes:
            provider_list.append({
                'name': provider['_id'],
                'prefixes': provider['prefixes']
            })

        for peer in peer_prefixes:
            peer_list.append({
                'name': peer['_id'],
                'prefixes': peer['prefixes']
            })

    return {
        'peer_type': peer_type_list,
        'customer_prefixes': customer_list,
        'provider_prefixes': provider_list,
        'peer_prefixes': peer_list,
        'country_distribute': country_distribute
    }


def format_list(return_list, data_prefixes, org_list):
    for item in data_prefixes:
        _list = [] + item['prefixes']
        o = {}
        for pfx in _list:
            pfx_l = pfx.split('/')
            pn = pfx_l[1]
            if '.' in pfx:
                if ':' not in pfx:
                    if 'ipv4_distribution' not in o:
                        o['ipv4_distribution'] = {}
                    if f'/{pn}' not in o['ipv4_distribution']:
                        o['ipv4_distribution'][f'/{pn}'] = 0
                    o['ipv4_distribution'][f'/{pn}'] += 1
            else:
                if 'ipv6_distribution' not in o:
                    o['ipv6_distribution'] = {}
                if f'/{pn}' not in o['ipv6_distribution']:
                    o['ipv6_distribution'][f'/{pn}'] = 0
                o['ipv6_distribution'][f'/{pn}'] += 1
        return_list.append({
            'name': item['_id'],
            'prefixes': o
        })
    rm = list(map(lambda x: x['name'], return_list))

    for org_as in org_list:
        if org_as not in rm:
            return_list.append({
                'name': org_as,
                'prefixes': {'ipv4_distribution': {}, 'ipv6_distribution': {}}
            })


@record_last_update_timestamp
def get_as_info_by_list_service(asn_list):
    a = app_dao.get_as_info_by_list_from_db(asn_list)
    returned_result = {}
    for i in a:
        asn_list.remove(int(i['_id']))
        returned_result[i['_id']] = {
            'org': i['organization']['orgName'] if i['organization'] and 'orgName' in i['organization'] else 'Unknown',
            'name': i['asnName'],
            'country': i['country']['iso'],
            'cone': i['cone']['numberAsns'],
            'rank': i['rank'],
            'announcingNumberAddresses': i['cone']['numberAddresses']
        }
    if len(asn_list) != 0:
        print(asn_list)
        whois_data = app_dao.get_as_info_by_list_from_whois(asn_list)
        finish_list = []
        for i in whois_data:
            asn = i['aut-num'][2:]
            if asn in finish_list:
                continue
            finish_list.append(asn)
            if asn not in returned_result:
                returned_result[asn] = {}
            if 'org' in i:
                returned_result[asn]['org'] = i['org']
            if 'as-name' in i:
                returned_result[asn]['name'] = i['as-name']
            if 'country' in i:
                returned_result[asn]['country'] = i['country']
            else:
                print(asn)
                if 'org' in i:
                    org_info = dashboard_dao.get_one_whois_info_by_org(i['org'])
                    if org_info and 'country' in org_info:
                        returned_result[asn]['country'] = org_info['country']
                if 'country' not in  returned_result[asn]:
                    nic_info = None
                    if 'admin-c' in i:
                        nic_info = dashboard_dao.get_one_whois_info_by_nic(i['admin-c'])
                    elif 'tech-c' in i:
                        nic_info = dashboard_dao.get_one_whois_info_by_nic(i['tech-c'])
                    if nic_info and 'country' in nic_info:
                        returned_result[asn]['country'] = nic_info['country']


    return returned_result


@record_last_update_timestamp
def asinfo_service(asn):
    a = app_dao.get_asinfo_from_db(asn)
    return a


@DeprecationWarning
def get_providers_4538_service():
    data = app_dao.get_providers_update_by_influx_db()
    # data = get_providers_4538_model()
    point_relation = {'4538': {'width': 1}}
    pass_point = ['4538']
    links = []
    for row in data:
        handle_providers_4538_data(row, point_relation, links, pass_point)
        # for index, point in enumerate(row['path'][1:6]):
        #     source = '4538'
        #     if '{' in point:
        #         continue
        #     if point not in pass_point:
        #         # print(point)
        #         pass_point.append(point)
        #         if index != 0:
        #             source = row['path'][1:6][index - 1]
        #         if source not in point_relation.keys():
        #             point_relation[source] = {'width': 1}
        #         point_relation[source][point] = {}
        #         point_relation[point] = {'width': 1}
        #         links.append({
        #             'source': source,
        #             'target': point
        #         })
    handle_point_relation('4538', point_relation)

    result = point_relation['4538']
    with open('4538.json', "a") as f:
        f.write(json.dumps({'4538': result}))
    return {
        'link': links,
        'result': result
    }


@record_last_update_timestamp
def get_real_time_in_a_while_service():
    real_time_data = app_dao.get_real_time_data_from_period()
    if len(real_time_data) == 0:
        real_time_data = app_dao.get_real_time_data_limit_last_3600()
    announced_v4_line = []
    announced_v6_line = []
    sum_v4 = 0
    count_v4 = 0
    sum_v6 = 0
    count_v6 = 0
    for i in real_time_data:
        i['_value'] = i['_value'].replace('\'', '\"')
        try:
            json_i = json.loads(i['_value'])
        except Exception as e:
            log.error(e)
            log.error('ERROR DATA %s' % i['_value'])
            continue
        date_stamp = int(i['_time'].timestamp() * 1000)
        # print(json_i)
        announced_v4_line.append([date_stamp, len(json_i['announced_v4'])])
        sum_v4 += len(json_i['announced_v4'])
        count_v4 += 1
        if 'announced_v6' in json_i.keys():
            announced_v6_line.append([date_stamp, len(json_i['announced_v6'])])
            sum_v6 += len(json_i['announced_v6'])
            count_v6 += 1
    if count_v4 == 0:
        count_v4 = 1
    if count_v6 == 0:
        count_v6 = 1
    return {
        'announced_v4_line': announced_v4_line,
        'announced_v6_line': announced_v6_line,
        'avg_v4': sum_v4 / count_v4,
        'avg_v6': sum_v6 / count_v6,
    }


@record_last_update_timestamp
def get_real_time_data_by_second():
    real_time_data = app_dao.get_real_time_data_by_second()

    announced_v4_line = []
    announced_v6_line = []

    for i in real_time_data:
        i['_value'] = i['_value'].replace('\'', '\"')
        json_i = json.loads(i['_value'])
        date_stamp = int(i['_time'].timestamp() * 1000)
        announced_v4_line.append([date_stamp, len(json_i['announced_v4'])])
        # sum_v4 += len(json_i['announced_v4'])
        if 'announced_v6' in json_i.keys():
            announced_v6_line.append([date_stamp, len(json_i['announced_v6'])])
            # sum_v6 += len(json_i['announced_v6'])
    return {
        'announced_v4_line': announced_v4_line,
        'announced_v6_line': announced_v6_line
    }


@record_last_update_timestamp
def get_as_list(asn):
    result = app_dao.get_as_list_by(asn)
    if not result:
        return {
            'customerAses': [],
            'providerAses': [],
            'peerAses': []
        }
    return {
        'customerAses': result['customer-ases'],
        'providerAses': result['provider-ases'],
        'peerAses': result['peer-ases']
    }


@record_last_update_timestamp
def get_as_path_by_prefix(input_value, asn, _type='v4'):
    condition = {
        'firstAs': asn,
        '$or': []
    }
    prefix = ipaddress.ip_network(input_value).exploded
    condition['$or'].append({'binary_prefix': {'$regex': f'{generate_subnet_regex(prefix)}'}})
    condition['$or'].append({'prefix': {'$in': generate_supernet_regex(prefix)}})

    log.debug(condition)
    print(condition)
    result = app_dao.get_as_path_by_condition(condition)

    amount_layer = []
    amount_links = []
    layerList = []
    will_return_obj = {}

    def transform_to_compressed(x):
        x_list = x.split('/')
        return f'{ipaddress.ip_address(x_list[0]).compressed}/{x_list[1]}'

    result_list = []
    for single_prefix in result:
        print(single_prefix)
        result_list.append(single_prefix)

    result_list.sort(key=lambda x: len(set(x['_id'].split(' '))), reverse=True)

    for single_prefix in result_list:
        links, layers = handle_layer_and_links(single_prefix['_id'].split(' '))
        # print(layers)
        prefix_key = '_'.join(map(transform_to_compressed, single_prefix['prefixes']))
        if prefix_key in will_return_obj.keys():
            if len(will_return_obj[prefix_key]['links']) > len(links):
                will_return_obj[prefix_key]['links'] = links
                will_return_obj[prefix_key]['layer'] = layers
            else:
                continue
        else:
            will_return_obj[prefix_key] = {'links': links,
                                           'layer': layers}
        # print(links)

    for prefix_key in will_return_obj:
        old_index = 0

        for index, l in enumerate(will_return_obj[prefix_key]['layer']):
            node_exist = False
            for layer_index in range(len(layerList)):
                if l in layerList[layer_index]:
                    old_index = layer_index + 1
                    node_exist = True
                    break

            if node_exist:
                continue

            if len(layerList) <= old_index:
                layerList.append(set())
                layerList[-1].add(l)
            else:
                layerList[old_index].add(l)
            old_index += 1

        # print(layerList)
        for link in will_return_obj[prefix_key]['links']:
            if link not in amount_links:
                amount_links.append(link)

    for i in range(len(layerList)).__reversed__():
        for point in layerList[i]:
            for j in range(i):
                if point in layerList[j]:
                    layerList[j].remove(point)

    for layer in layerList:
        # if len(layer) != 0:
        amount_layer.append(list(layer))

    return {
        'result': will_return_obj,
        'layer': amount_layer,
        'links': amount_links
    }


# 从左到右1的个数以及对应十进制的值
number_of_1_map = {
    1: 128,
    2: 192,
    3: 224,
    4: 240,
    5: 248,
    6: 252,
    7: 254,
    8: 255,
}

number_of_1_map_v6 = {
    1: 32768,
    2: 49152,
    3: 57344,
    4: 61440,
    5: 63488,
    6: 64512,
    7: 65024,
    8: 65280,
    9: 65408,
    10: 65472,
    11: 65504,
    12: 65520,
    13: 65528,
    14: 65532,
    15: 65534,
    16: 65535,
}


def generator_regex_express_v4(input_list):
    ip = input_list[0]
    v4_each_segment_b_num = 8
    max_prefix = (4 - 1) * v4_each_segment_b_num
    ip_segments = ip.split('.')
    ip_segments[-1] = '0'
    ip_segments_superset = ip_segments.copy()
    prefix = max_prefix
    if len(input_list) == 2:
        prefix = int(input_list[1])
    prefix_regex = '(' + '|'.join(map(lambda x: str(x), range(prefix, max_prefix + 1))) + ')$'
    min_ip_segments = 0
    # 确定IP最大可以更新到第几段
    segment_index = int(prefix / v4_each_segment_b_num)
    superset_prefix = prefix
    # # superset_regex
    # 找ipv4 前三段 所有可能的IP
    for i in range(int(max_prefix / v4_each_segment_b_num)):
        # 如果还没到就跳过
        if i < segment_index:
            continue
        # 如果超过了，就用最大值
        if i > segment_index:
            superset_prefix = (i + 1) * v4_each_segment_b_num
        # superset_prefix可能是根据输入前缀算出来的，也可能是最大值
        # 如果实际对应IP段的值比根据超集的网络号算出来的最大主机号要大或者一样，就认为循环到了prefix对应的IP段
        if int(ip_segments_superset[i]) >= 1 << (v4_each_segment_b_num - (superset_prefix % v4_each_segment_b_num)):
            # 按照输出前缀计算最小的主机号
            min_ip_segments = int(ip_segments_superset[i]) & number_of_1_map[prefix % v4_each_segment_b_num]
        # 按照输出前缀计算最大的主机号
        max_ip_segments = (1 << (v4_each_segment_b_num - (superset_prefix % v4_each_segment_b_num)))
        # 从最小主机号到最大主机号都是超集，设置每段IP的超集
        ip_segments_superset[i] = '(' + '|'.join(
            map(lambda x: str(x), range(min_ip_segments, min_ip_segments + max_ip_segments))) + ')'
    superset_regex = '(^' + '\\.'.join(ip_segments_superset) + '\\/' + prefix_regex + ')'

    subset_regex_list = []
    ip_segments_subset = ip_segments.copy()
    # 把prefix对应的IP段及以上设置为0
    for index in range(4 - math.ceil(prefix / v4_each_segment_b_num)):
        ip_segments_subset[-(index + 1)] = "0"

    # 从prefix循环到8 [8,prefix)
    for sub_prefix in range(8, prefix).__reversed__():
        # 计算对应的sub_prefix所在的IP段下标
        subset_segment_index = int(sub_prefix / 8)
        # 对应IP段1的数量
        one_num = sub_prefix % v4_each_segment_b_num
        if one_num == 0:
            diff = 0
        else:
            # 计算从左到右有one_num个1的时候十进制的值
            # 10000000
            # 11000000
            # 11100000
            # 11110000
            diff = (1 << v4_each_segment_b_num) - (1 << (v4_each_segment_b_num - one_num))

        # 只保留到对应diff 1的位置
        ip_segments_subset[subset_segment_index] = diff & int(ip_segments_subset[subset_segment_index])
        # 生成对应sub_prefix的前缀
        subset_regex_list.append('^' + '\\.'.join(map(lambda x: str(x), ip_segments_subset)) + '\\/' + str(sub_prefix))
    subset_regex = '(' + '|'.join(subset_regex_list) + ')'

    if prefix == 8:
        return superset_regex
    else:
        return '|'.join([superset_regex, subset_regex])


def to_hex(num):
    # result = hex(int(num, 16))[2::]
    # if result == "0":
    #     result = ''
    return num


def make_hex_regex(min_value_10, max_value_10):
    # print(minV_10, maxV_10)
    common_regex = '[0-f]'
    min_num = 0
    max_hex_num = 'f'
    minV_list = list(str(hex(min_value_10)[2::]))
    maxV_list = list(str(hex(max_value_10)[2::]))
    min_diff = 4 - len(minV_list)
    range2 = max(len(minV_list), len(maxV_list))
    if min_diff > 0:
        minV_list = ["0"] * min_diff + minV_list

    max_diff = 4 - len(maxV_list)
    if max_diff > 0:
        maxV_list = ["0"] * max_diff + maxV_list
    # print(minV_list)
    # print(maxV_list)
    regex_list = []
    for i in range(1, range2):
        if i == 1:  # 最后一个，要包含本身
            if int(minV_list[-i], 16) == 15:
                regex_list = ['%s[%s]' % (to_hex(''.join(minV_list[:-i])), minV_list[-i])] + regex_list
            elif int(minV_list[-i], 16) + 1 < 10:
                regex_list = ['%s[%s-%s]' % (to_hex(''.join(minV_list[:-i])), minV_list[-i], max_hex_num)] + regex_list
            else:
                regex_list = ['%s[%s-%s]' % (to_hex(''.join(minV_list[:-i])), minV_list[-i], max_hex_num)] + regex_list

            if int(maxV_list[-i], 16) == 0:

                regex_list = ['%s[%s]' % (to_hex(''.join(maxV_list[:-i])), maxV_list[-i])] + regex_list
            elif int(maxV_list[-i], 16) >= 10:
                regex_list = ['%s[%s-%s]' % (to_hex(''.join(maxV_list[:-i])), min_num, maxV_list[-i])] + regex_list
            else:
                regex_list = ['%s[%s-%s]' % (to_hex(''.join(maxV_list[:-i])), min_num, maxV_list[-i])] + regex_list
        else:

            if int(minV_list[-i], 16) == 15:
                regex_list = ['%s[f]%s' % (
                    to_hex(''.join(minV_list[:-i])),
                    ''.join(['[f]' for _ in range(i - 1)]))] + regex_list
            else:
                regex_list = ['%s[%s-%s]%s' % (
                    to_hex(''.join(minV_list[:-i])), str(hex(int(minV_list[-i], 16) + 1))[2::], max_hex_num,
                    ''.join([common_regex for _ in range(i - 1)]))] + regex_list

            if int(maxV_list[-i], 16) == 0:
                regex_list = ['%s[0]%s' % (
                    to_hex(''.join(maxV_list[:-i])),
                    ''.join(['[0]' for _ in range(i - 1)]))] + regex_list
            else:
                regex_list = ['%s[%s-%s]%s' % (
                    to_hex(''.join(maxV_list[:-i])), min_num, str(hex(int(maxV_list[-i], 16) - 1))[2::],
                    ''.join([common_regex for _ in range(i - 1)]))] + regex_list

    if hex(int(minV_list[-range2], 16) + 1)[2::] <= hex(int(maxV_list[-range2], 16) - 1)[2::]:
        s = "%s[%s-%s]%s" % (
            ''.join(['0' for _ in range(4 - range2)]), hex(int(minV_list[-range2], 16) + 1)[2::],
            hex(int(maxV_list[-range2], 16) - 1)[2::],
            ''.join([common_regex for _ in range(range2 - 1)]))
        regex_list = [s] + regex_list

    # print(regex_list)
    return "(%s)" % '|'.join(regex_list)


def generator_regex_express_v6(input_list):
    ip = ipaddress.ip_address(input_list[0]).exploded
    v6_each_segment_b_num = 16
    max_prefix = 7 * v6_each_segment_b_num
    ip_segments = ip.split(':')
    ip_segments[-1] = '0000'
    ip_segments_superset = ip_segments.copy()
    prefix = max_prefix
    if len(input_list) == 2:
        prefix = int(input_list[1])
    prefix_regex = '(' + '|'.join(map(lambda x: str(x), range(prefix, max_prefix + 1))) + ')$'

    # 确定IP最大可以更新到第几段
    segment_index = int(prefix / v6_each_segment_b_num)
    superset_prefix = prefix
    # # superset_regex
    # 找ipv4 前三段 所有可能的IP
    for i in range(int(max_prefix / v6_each_segment_b_num)):
        min_ip_segments = 0
        # 如果还没到就跳过
        if i < segment_index:
            continue
        # 如果超过了，就用最大值
        if i > segment_index:
            superset_prefix = (i + 1) * v6_each_segment_b_num
        # superset_prefix可能是根据输入前缀算出来的，也可能是最大值
        # 如果实际对应IP段的值比根据超集的网络号算出来的最大主机号要大或者一样，就认为循环到了prefix对应的IP段
        if int(ip_segments_superset[i], 16) >= 1 << (v6_each_segment_b_num - (superset_prefix % v6_each_segment_b_num)):
            # 按照输出前缀计算最小的主机号
            min_ip_segments = int(ip_segments_superset[i], 16) & number_of_1_map_v6[prefix % v6_each_segment_b_num]
            # print(ip_segments_superset[i], number_of_1_map[prefix % v6_each_segment_b_num])
        # 按照输出前缀计算最大的主机号
        # print(superset_prefix, (superset_prefix % v6_each_segment_b_num))
        max_ip_segments = (1 << (v6_each_segment_b_num - (superset_prefix % v6_each_segment_b_num)))
        # 从最小主机号到最大主机号都是超集，设置每段IP的超集

        ip_segments_superset[i] = make_hex_regex(min_ip_segments, min_ip_segments + max_ip_segments - 1)
        # print(min_ip_segments, max_ip_segments - 1, ip_segments_superset[i])

    superset_regex = '(^' + ':'.join(ip_segments_superset) + '\\/' + prefix_regex + ')'
    # print(superset_regex)
    subset_regex_list = []
    ip_segments_subset = ip_segments.copy()
    # 把prefix对应的IP段及以上设置为0
    for index in range(8 - math.ceil(prefix / v6_each_segment_b_num)):
        ip_segments_subset[-(index + 1)] = "0000"

    # 从prefix循环到8 [8,prefix)
    for sub_prefix in range(8, prefix).__reversed__():
        # 计算对应的sub_prefix所在的IP段下标
        subset_segment_index = int(sub_prefix / v6_each_segment_b_num)
        # 对应IP段1的数量
        one_num = sub_prefix % v6_each_segment_b_num
        if one_num == 0:
            diff = 0
        else:
            # 计算从左到右有one_num个1的时候十进制的值
            # 10000000
            # 11000000
            # 11100000
            # 11110000
            diff = (1 << v6_each_segment_b_num) - (1 << (v6_each_segment_b_num - one_num))

        # 只保留到对应diff 1的位置
        ip_segments_subset[subset_segment_index] = hex(diff & int(ip_segments_subset[subset_segment_index], 16))[2::]
        ip_segment_diff = 4 - len(ip_segments_subset[subset_segment_index])
        if ip_segment_diff > 0:
            ip_segments_subset[subset_segment_index] = '0' * ip_segment_diff + ip_segments_subset[subset_segment_index]

        # 生成对应sub_prefix的前缀
        subset_regex_list.append('^' + ':'.join(map(lambda x: str(x), ip_segments_subset)) + '\\/' + str(sub_prefix))

    subset_regex = '(' + '|'.join(subset_regex_list) + ')'

    if len(subset_regex_list) == 0:
        subset_regex = ''

    if prefix == 8:
        return superset_regex
    elif subset_regex:
        return '|'.join([superset_regex, subset_regex])
    else:
        return superset_regex


def handle_layer_and_links(path):
    layerList = []
    links = []
    layers = []

    for index, point in enumerate(path):
        if len(layerList) <= index:
            layerList.append(set())
        layerList[index].add(point)

    for i in range(len(layerList) - 1):
        for source in list(layerList[i]):
            for target in list(layerList[i + 1]):
                links.append({
                    'source': source,
                    'target': target
                })

    for layer in layerList:
        layers += list(layer)
    return links, layers


@record_last_update_timestamp
def get_resilience_by_cc_code(cc):
    as_list = []
    cone_map = {}
    graph_data = {"peer": [], "customer": []}
    result = app_dao.get_cc2as_by_cc(cc)

    for i in result:
        as_list.append(i['_id'])
        cone_map[i['_id']] = i['cone']['numberAsns']

    as_relationship = app_dao.get_as_relationship_by_as_list(as_list)

    for i in as_relationship:
        for peer in i['peer-ases']:
            graph_data['peer'].append([i['_id'], peer])
        for customer in i['customer-ases']:
            graph_data['customer'].append([i['_id'], customer])

    return {
        'cone': cone_map,
        'graph_data': graph_data
    }


def sort_changed_as(a):
    return -(a['to_origin_increase'] + a['to_origin_decrease'])


@record_last_update_timestamp
def get_prefix_total_by_asn(asn):
    total = app_dao.get_prefix_total_by_asn(asn)
    return {
        'total': total
    }


async def fetch(session, ases):
    async with session.get(GET_AS_DIFF_API, params={'asns': ','.join(ases), 'date': '20221219'}) as response:
        return await response.text()


async def get_as_diff(ases, changed_as, unchanged_as):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, ases)
        json_body = json.loads(html)
        for As in json_body:
            if 'summary' in As.keys():
                o = As['summary']
                o['_id'] = As['_id']
                o['to_origin'] = As['to_origin']
                changed_as.append(o)
            else:
                o = As
                unchanged_as.append(o)


@record_last_update_timestamp
def down_load_as_diff(url):
    real_url = str(base64.b64decode(url), 'utf-8')
    regex = re.compile(r'.*?asn=(?P<ASN>\d+).*?date=(?P<date>\d+)$')
    m = regex.match(real_url)
    file_name = 'as-diff'
    if m:
        asn = m.group('ASN')
        date = m.group('date')
        file_name = '%s-%s-%s.txt' % (file_name, asn, date)
    response = requests.get(real_url)
    return response.content, file_name


def make_links_and_name(dataset, asn):
    name_map = {}
    name = []
    links = []
    row = [str(i) for i in dataset['row']]
    col = [str(i) for i in dataset['col']]
    link = list(zip(row, col))
    # print(link)
    for ll in link:
        a, b = ll
        name_map[a] = 1
        name_map[b] = 1

        links.append({
            'source': b,
            'target': a
        })

    for i in name_map:
        o = {'name': i}
        if i == asn:
            o = {'name': i,
                 'itemStyle': {
                     'color': 'red'
                 }}

        name.append(o)
    return name, links


@record_last_update_timestamp
def get_topology_data(cc, asn):
    cc_path = os.path.join('resilience_data/rtree', cc, 'dcomplete%s.npz' % asn)
    dataset = numpy.load(cc_path, allow_pickle=True)
    name, links = make_links_and_name(dataset, asn)
    return {
        'name': name,
        'links': links
    }


@record_last_update_timestamp
def get_as_by_cc(cc):
    cc_path = os.path.join('resilience_data/rtree', cc)
    as_list = os.listdir(cc_path)
    result = []
    for fn in as_list:
        if 'npz' == fn[-3:]:
            asn = fn[9:-4]
            result.append({'value': asn})
            print(asn)
    return result


@record_last_update_timestamp
def get_topology_data_optimize(cc, asn):
    a = {}
    cc_path = os.path.join('resilience_data/rtree', cc, 'dcomplete%s.npz' % asn)
    optimize_cc_path = os.path.join('resilience_data/optimize', cc, 'dcomplete%s.npz' % asn)
    dataset = numpy.load(cc_path, allow_pickle=True)
    dataset_opt = numpy.load(optimize_cc_path, allow_pickle=True)
    name, links = make_links_and_name(dataset, asn)
    name_opt, links_opt = make_links_and_name(dataset_opt, asn)
    for i in links_opt:
        if str(i) not in a:
            a[str(i)] = 0
        a[str(i)] += 1
    for ii in a:
        print(ii, a[ii])

    for i in links_opt:
        if i not in links:
            i['lineStyle'] = {'color': 'red'}
    # print(links)

    return {
        'name': name,
        'links': links,
        'name_opt': name_opt,
        'links_opt': links_opt,
    }


@record_last_update_timestamp
def get_rtree_by_asn(cc: str, asn: str, condition: str) -> Dict[str, str]:
    try:
        cone_condition = None
        output_path = 'static'
        graph_format = 'png'
        if ('[' in condition or '(' in condition) and (']' in condition or ')' in condition):
            cone_condition = condition
            graph_path = os.path.join(output_path, f'dcomplete{asn}-{cone_condition}.{graph_format}')
        else:
            graph_path = os.path.join(output_path, f'dcomplete{asn}.{graph_format}')
        if not os.path.exists(graph_path):
            graph_path = draw_rtree(asn, cc, output_path, graph_format, cone_condition)

        with open(graph_path, 'rb') as f:
            image_byte = f.read()
            base64_code = base64.b64encode(image_byte).decode()

        return {'base64_code': f'data:image/png;base64,{base64_code}'}
    except Exception:
        return {
            'base64_code': 'Blank'}


@record_last_update_timestamp
def get_rtree_by_prefix(prefix):
    msg = 'Invalid IP/Prefix'

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

    graph_format = 'png'

    try:
        condition = {
            '$or': []
        }
        condition['$or'].append({'binary': {'$regex': f'{generate_subnet_regex(prefix)}'}})
        condition['$or'].append({'_id': {'$in': generate_supernet_regex(prefix)}})
        hash_info = routing_path_dao.get_one_hash_by_condition(condition)

    except Exception as e:
        log.error(e)
        return {'base64_code': 'Error',
                'msg': msg}

    prefix_name = org_prefix.replace('/', '-')

    if hash_info:
        hash_value = hash_info['Hash']
        rtree_info = routing_path_dao.get_rtree_by_hash(hash_value)
        output_path = 'static'
        # print(rtree_info)
        links = rtree_info['edges']
        nodes = list(links.keys()) + rtree_info['Allroots']
        roots = rtree_info['Allroots']
        print(nodes)

        nodes.append('org_prefix')

        links['org_prefix'] = roots

        formatted_link: List[LinkType] = []

        if len(nodes) != 0 and len(links) != 0:
            for left_as in links:
                for right_as in links[left_as]:
                    formatted_link.append(LinkType((right_as, left_as)))

            log.debug(formatted_link)
            png_path = os.path.join(output_path, f'{prefix_name}.{graph_format}')
            if not os.path.exists(png_path):
                png_path = draw_graph_by_prefix(prefix_name, nodes, formatted_link, 'static')
            with open(png_path, 'rb') as f:
                image_byte = f.read()
                base64_code = base64.b64encode(image_byte).decode()
            return {'base64_code': f'data:image/png;base64,{base64_code}'}
    else:
        msg = f'{prefix} Not Found'

    return {'base64_code': 'Error',
            'msg': msg}


@record_last_update_timestamp
def get_route_by_prefix(left_ip, right_ip):
    l_links = []
    l_nodes = [[]]
    r_links = []
    r_nodes = [[]]

    final_left_condition, left_input_list = get_regex_by_ip(left_ip)
    final_right_condition, right_input_list = get_regex_by_ip(right_ip)
    # print(final_right_condition)
    # print(final_left_condition)
    left_rtree_hash_list = routing_path_dao.get_route_by_condition(final_left_condition)
    right_rtree_hash_list = routing_path_dao.get_route_by_condition(final_right_condition)
    # ii_l = []

    # for i in left_rtree_hash_list:
    #     print(i)

    if left_rtree_hash_list.count() and right_rtree_hash_list.count():
        left_rtree_hash = min(left_rtree_hash_list,
                              key=lambda x: abs(int(x['_id'].split('/')[-1]) - int(left_input_list[-1])))

        right_rtree_hash = min(right_rtree_hash_list,
                               key=lambda x: abs(int(x['_id'].split('/')[-1]) - int(right_input_list[-1])))

        if left_rtree_hash['Hash'] == -1:
            return {'status': False, 'msg': f'Not Found prefix {left_ip}'}
        if right_rtree_hash['Hash'] == -1:
            return {'status': False, 'msg': f'Not Found prefix {right_ip}'}
        left_rtree = routing_path_dao.get_rtree_by_hash(left_rtree_hash['Hash'])
        print(left_rtree_hash)
        right_rtree = routing_path_dao.get_rtree_by_hash(right_rtree_hash['Hash'])
        print(right_rtree_hash)

        if right_rtree:
            right_path_dict = make_path_dict(right_rtree, right_ip)
        else:
            right_path_dict = {right_rtree_hash['AS'][0]: right_rtree_hash['AS']}
        if left_rtree:
            left_path_dict = make_path_dict(left_rtree, left_ip)
        else:
            left_path_dict = {left_rtree_hash['AS'][0]: left_rtree_hash['AS']}

        # print(left_rtree['Allroots'])
        # print(right_path_dict)
        # for i in right_path_dict:
        #     print(i, right_path_dict[i])

        if not left_rtree:
            left_rtree = {'Allroots': left_rtree_hash['AS']}
        for node in left_rtree['Allroots']:

            if str(node) in right_path_dict:
                shortest_path = right_path_dict[str(node)]
                r_nodes = [[i] for i in shortest_path]
                # r_nodes.reverse()
                for i in range(len(shortest_path) - 1):
                    r_links.append({'target': shortest_path[i], 'source': shortest_path[i + 1]})

        if not right_rtree:
            right_rtree = {'Allroots': right_rtree_hash['AS']}

        for node in right_rtree['Allroots']:
            
            if str(node) in left_path_dict:
                shortest_path = left_path_dict[str(node)]
                l_nodes = [[i] for i in shortest_path]
                # l_nodes.reverse()
                for i in range(len(shortest_path) - 1):
                    l_links.append({'target': shortest_path[i], 'source': shortest_path[i + 1]})

        # make_links_for_ip2ip(right_rtree['Allroots'], l_links, l_nodes, left_rtree)
        # make_links_for_ip2ip(left_rtree['Allroots'], r_links, r_nodes, right_rtree)
    r_nodes.reverse()
    return {
        'l2r': {
            'nodes': l_nodes,
            'links': l_links
        },
        'r2l': {
            'nodes': r_nodes,
            'links': r_links
        }

    }


def make_path_dict(rtree: Dict, ip: str) -> Dict:
    links = rtree['edges']
    # nodes = rtree['nodes']
    roots = rtree['Allroots']
    links[ip] = roots
    point_relation: Dict = {}
    if len(links) != 0:
        for left_as in links:
            point_relation[left_as] = {}
            for right_as in links[left_as]:
                point_relation[left_as][str(right_as)] = {}

    aggregate_point_relation(ip, point_relation)

    path_dict: Dict[str, List] = {}
    for r in roots:
        recursive_for_point_relation(str(r), point_relation, 1, path_dict)
    # print(len(point_relation), point_relation)
    for i in path_dict:
        # print(i,path_dict[i])
        path_dict[i] = min(path_dict[i], key=lambda x: len(x))

    return path_dict


def make_links_for_ip2ip(roots, links, nodes, rtree):
    for i in roots:
        nodes[-1].append(str(i))

    for root in roots:
        find_present_node_in_tree(rtree['edges'], root, links, nodes)
    if len(nodes) == 1:
        nodes.append([])
        for i in rtree['Allroots']:
            nodes[-1].append(str(i))


def find_present_node_in_tree(tree, node, links, nodes):
    for k in tree:
        if int(node) in tree[k]:
            links.append({'target': str(k), 'source': str(node)})
            nodes.insert(0, [str(k)])
            find_present_node_in_tree(tree, k, links, nodes)
            break


@record_last_update_timestamp
def getAsInfo(asn, as_name, org_name):
    result = app_dao.get_as_info(asn, as_name, org_name)
    return_list = []
    for i in result:
        return_list.append({
            'asn': i['_id'].__str__(),
            'as_name': f"{i['asnName']} ({i['country']['iso']})",
            'org_name': i['organization']['orgName'],
            'cone': i['cone']['numberAsns'],
        })
    return return_list
