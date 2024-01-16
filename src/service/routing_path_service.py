import ipaddress
from typing import List, Dict

from src.service.util import generate_subnet_regex, generate_supernet_regex, record_last_update_timestamp, get_regex_by_ip
from src.model import routing_path_dao, app_dao
from src.service.draw_rtree import LinkType
from src.utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)


def recursive_for_point_relation(_k, _point_relation, layer, path_dict, node_list=None, pass_list=None):
    if pass_list is None:
        pass_list = []
    if node_list is None:
        node_list = []
    node_list.append(_k)

    path_dict.setdefault(_k, [])
    path_dict[_k].append([*node_list])
    for kk in _point_relation[_k]:
        if kk not in pass_list:
            pass_list.append(kk)
            recursive_for_point_relation(kk, _point_relation[_k], layer + 1, path_dict, node_list, pass_list)
            node_list.remove(kk)


@record_last_update_timestamp
def get_rtree_by_prefix(prefix):
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
    # graph_format = 'png'

    try:
        condition = {
            '$or': []
        }
        condition['$or'].append({'binary': {'$regex': f'{generate_subnet_regex(prefix)}'}})
        condition['$or'].append({'_id': {'$in': generate_supernet_regex(prefix)}})

        hash_info_list = routing_path_dao.get_route_by_condition(condition)
        if not hash_info_list.count():
            return {'base64_code': 'Error',
                    'msg': 'Not Found IP/Prefix',
                    'status': 'failed'}
        hash_info = min(hash_info_list,
                        key=lambda x: abs(int(x['_id'].split('/')[-1]) - int(prefix_list[-1])))
    except Exception as e:
        return {'base64_code': 'Error',
                'msg': 'Invalid IP/Prefix',
                'status': 'failed'}

    if not hash_info:
        return {'base64_code': ''}
    print(hash_info)
    hash_value = hash_info['Hash']
    if hash_value == -1 or hash_value == '-1':
        return {'prefix': org_prefix, 'categories': ['layer0'], 'links': [], 'nodes': [{
            'name': org_prefix,
            'category': 0
        }], 'path_dict': {}}
    rtree_info = routing_path_dao.get_rtree_by_hash(hash_value)
    print(rtree_info)
    links = rtree_info['edges']
    # nodes = rtree_info['nodes']
    roots = rtree_info['Allroots']

    # nodes.append(org_prefix)

    links[org_prefix] = roots

    formatted_link: List[LinkType] = []
    point_relation: Dict = {}
    if len(links) != 0:
        for left_as in links:
            point_relation[left_as] = {}
            for right_as in links[left_as]:
                point_relation[left_as][str(right_as)] = {}
                formatted_link.append(LinkType((str(right_as), str(left_as))))

    aggregate_point_relation(org_prefix, point_relation)
    categories = set()
    result_node: List[Dict] = [{
        'name': org_prefix,
        'category': 0
    }]
    path_dict: Dict[str, List] = {}
    for r in roots:
        recursive_for_point_relation(str(r), point_relation, 1, path_dict)
    for i in path_dict:
        path_dict[i] = [org_prefix] + min(path_dict[i], key=lambda x: len(x))
    for i in path_dict:
        oo = {
            'name': str(i),
            'category': len(path_dict[i]) - 2
        }
        result_node.append(oo)
        categories.add(f"layer{oo['category']}")

    categories = list(categories)
    categories.sort(key=lambda x: x[5:])
    result_node.sort(key=lambda x: x['category'], reverse=True)
    return {'nodes': result_node, 'links': formatted_link, 'prefix': org_prefix, 'categories': categories, 'path_dict': path_dict,
            'date': routing_path_dao.get_date_of_date()}


def aggregate_point_relation(asn, point_relation, pass_List=None):
    if pass_List is None:
        pass_List = []
    if not point_relation:
        return point_relation
    if point_relation[asn] == {}:
        return point_relation[asn]

    for key in point_relation[asn].keys():
        if key in point_relation.keys():
            if key not in pass_List:
                pass_List.append(key)
                temp = aggregate_point_relation(key, point_relation, pass_List)
                point_relation[asn][key].update(temp)

    return point_relation[asn]


# deprecate
@record_last_update_timestamp
def get_rtree_by_prefix_data_to_topo(prefix):
    pass
    org_prefix = prefix
    prefix_list = prefix.split('/')
    if ':' in prefix:
        prefix_list[0] = ipaddress.ip_address(prefix_list[0]).exploded
        prefix = '/'.join(prefix_list)

    try:
        prefix_network = ipaddress.ip_network(prefix)
    except Exception as e:
        return {'base64_code': 'Error',
                'msg': 'Invalid IP/Prefix'}

    searched_prefix = prefix_network.exploded

    hash_info = routing_path_dao.get_hash_by_prefix(searched_prefix.__str__())
    # 如果输入的找不到
    if not hash_info:
        # 先找超集
        for i in range(prefix_network._prefixlen - 1):
            searched_prefix = prefix_network.supernet(prefixlen_diff=i + 1)
            hash_info = routing_path_dao.get_hash_by_prefix(searched_prefix.exploded.__str__())
            print(hash_info, searched_prefix.exploded)
            if hash_info:
                org_prefix = searched_prefix.__str__()
                break
        if not hash_info:
            # 再找超集
            for i in range(prefix_network.max_prefixlen - prefix_network._prefixlen + 1):
                for ii in prefix_network.subnets(i):
                    hash_info = routing_path_dao.get_hash_by_prefix(ii.exploded.__str__())
                    print(hash_info, ii.exploded)
                    if hash_info:
                        org_prefix = ii.__str__()
                        break
                if hash_info:
                    break

    if not hash_info:
        return {'base64_code': ''}
    hash_value = hash_info['Hash']
    rtree_info = routing_path_dao.get_rtree_by_hash(hash_value)

    links = rtree_info['edges']
    nodes = rtree_info['nodes']
    roots = rtree_info['Allroots']

    nodes.append(org_prefix)

    links[org_prefix] = roots

    formatted_link: List = []

    point_relation: Dict = {}
    if len(nodes) != 0 and len(links) != 0:
        for left_as in links:
            point_relation[left_as] = {'width': 1}
            for right_as in links[left_as]:
                point_relation[left_as][str(right_as)] = {}
                formatted_link.append({'source': str(right_as), 'target': str(left_as)})
        # formatted_link.append(LinkType((roots[0], org_prefix)))

    handle_point_relation(org_prefix, point_relation)

    return {
        'link': formatted_link,
        'result': point_relation[org_prefix]
    }


@record_last_update_timestamp
def get_routing_path_cluster(asn):
    try:
        int(asn)
    except ValueError:
        return {
            'status': 'failed',
            'statusCode': 'Invalid ASN'
        }
    result: List = []
    data = routing_path_dao.get_cluster_info_by_asn(int(asn))
    count = 1
    for cluster_hash in data['Cluster']:
        if cluster_hash == 'all_Hashes':
            continue
        o = {'cluster_hash': cluster_hash, 'name': f'Cluster{count}', 'rtree_list': []}

        for rtree in data['Cluster'][cluster_hash]['Hashes']:
            o['rtree_list'].append({'hash': str(rtree[0]), 'prefix_list': rtree[1]})
            # print(rtree[0], data['Cluster'][cluster_hash]['Type'])
        result.append(o)
        count += 1
    return {'result': result}


@record_last_update_timestamp
def get_rtree_by_hash(_hash):
    try:
        _hash = int(_hash)
    except ValueError:
        return {
            'status': 'failed',
            'statusCode': 'Invalid Hash'
        }
    rtree_info = routing_path_dao.get_rtree_by_hash(_hash)
    links = rtree_info['edges']
    nodes = rtree_info['nodes']
    roots = rtree_info['ASroots']

    formatted_link: List[LinkType] = []
    point_relation: Dict = {}
    if len(nodes) != 0 and len(links) != 0:
        for left_as in links:
            point_relation[left_as] = {}
            for right_as in links[left_as]:
                point_relation[left_as][str(right_as)] = {}
                formatted_link.append(LinkType((str(right_as), str(left_as))))

    for i in roots:
        aggregate_point_relation(str(i), point_relation)

    categories = set()
    nodeSet = set()
    # categories.add()
    result_node: List[Dict] = []
    path_dict: Dict[str, List] = {}
    for i in roots:
        recursive_for_point_relation(str(i), point_relation, 1, path_dict)

    for i in path_dict:
        path_dict[i] = min(path_dict[i], key=lambda x: len(x))
    for i in path_dict:
        oo = {
            'name': str(i),
            'category': len(path_dict[i]) - 1
        }
        result_node.append(oo)
        categories.add(f"layer{oo['category']}")

    categories = list(categories)
    categories.sort(key=lambda x: x[5:])
    return {'nodes': result_node, 'links': formatted_link, 'asn': roots[0], 'categories': categories, 'path_dict': path_dict}


@record_last_update_timestamp
def get_rtree_by_hashes(hashes, asn):
    links = {}
    nodes = []
    roots = []
    for h in hashes:
        try:
            _hash = int(h)
        except ValueError:
            return {
                'status': 'failed',
                'statusCode': 'Invalid Hash'
            }

        rtree_info = routing_path_dao.get_rtree_by_hash(_hash)
        if not rtree_info or int(asn) not in rtree_info['ASroots']:
            continue
        for i in rtree_info['edges']:
            links.setdefault(i, [])
            links[i] += rtree_info['edges'][i]
        nodes += rtree_info['nodes']
        roots += rtree_info['ASroots']

    for i in links:
        links[i] = list(set(links[i]))
    # links = list(set(links))
    nodes = list(set(nodes))
    roots = list(set(roots))

    formatted_link: List[LinkType] = []
    point_relation: Dict = {}
    if len(nodes) != 0 and len(links) != 0:
        for left_as in links:
            point_relation[left_as] = {}
            for right_as in links[left_as]:
                point_relation[left_as][str(right_as)] = {}
                formatted_link.append(LinkType((str(right_as), str(left_as))))

    for i in roots:
        aggregate_point_relation(str(i), point_relation)

    categories = set()
    # nodeSet = set()

    result_node: List[Dict] = []
    path_dict: Dict[str, List] = {}
    # for i in roots:
    recursive_for_point_relation(asn, point_relation, 1, path_dict)
    for i in path_dict:
        path_dict[i] = min(path_dict[i], key=lambda x: len(x))
    for i in path_dict:
        oo = {
            'name': str(i),
            'category': len(path_dict[i]) - 1
        }
        result_node.append(oo)
        categories.add(f"layer{oo['category']}")

    categories = list(categories)
    categories.sort(key=lambda x: x[5:])
    result_node.sort(key=lambda x: x['category'], reverse=True)
    print('len(formatted_link)', point_relation)
    return {'nodes': result_node, 'links': formatted_link, 'asn': asn, 'categories': categories, 'path_dict': path_dict}


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


def get_bi_prefix_by_another_prefix(prefix):
    condition, input_list = get_regex_by_ip(prefix)
    rtree_info = routing_path_dao.get_route_by_condition(condition)
    hashes = None
    if rtree_info.count():
        for info in rtree_info:
            _hash = info['Hash']
            rtree = routing_path_dao.get_rtree_by_hash(_hash)
            l = routing_path_dao.get_matched_hash_by_rtree(rtree)

            # try:
            #     hashes = next(routing_path_dao.get_matched_hash_by_rtree(rtree))['hash']
            # except Exception as e:
            #     print(e)
            # print(hashes)
            # if hashes:

    return {}


@record_last_update_timestamp
def get_jitter_top_n_prefix_by_as(asn, st, et, source):
    result = routing_path_dao.get_jitter_top_n_prefix_by_as(asn, st, et, source)
    _list = []
    for i in result:
        try:
            i['prefix'] = str(ipaddress.ip_network(i['_id'].strip('\n')))
        except Exception as e:
            i['prefix'] = i['_id'].strip('\n')
        i['K'] = i['prefix']
        i['V'] = i['sum']
        del i['_id']
        _list.append(i)
    return _list


@record_last_update_timestamp
def get_jitter_data_by_prefix(asn, prefix, st, et, source):
    ip, pfx = prefix.split('/')
    prefix = f'{ipaddress.ip_address(ip).exploded}/{pfx}'
    result = routing_path_dao.get_jitter_data_by_prefix(asn, prefix, st, et, source)
    record = {'as_path_list': [], 'A_list': [], 'W_list': [], 'F_list': []}
    s = 0
    for i in result:
        s += 1
        record['as_path_list'].append(i['raws'])
        record['A_list'].append(i['A'])
        record['W_list'].append(i['W'])
        record['F_list'].append(i['F'])
    print(s)
    # try:
    #     record = next(result)
    # except Exception:
    #     pass
    record['A_list'].reverse()
    record['F_list'].reverse()
    record['W_list'].reverse()
    return record


@record_last_update_timestamp
def get_jitter_top_n_peer_by_as(asn, st, et, source):
    result = routing_path_dao.get_jitter_top_n_peer_by_as(asn, st, et, source)
    _list = []
    for i in result:
        i['K'] = i['_id']
        i['V'] = i['A']
        del i['_id']
        del i['A']
        _list.append(i)
    return _list


@record_last_update_timestamp
def get_jitter_data_by_peer_asn(asn, peer, st, et, source):
    result = routing_path_dao.get_jitter_data_by_peer_asn(asn, peer, st, et, source)
    try:
        record = next(result)
        del record['_id']
        return record
    except Exception as e:
        return {}


@record_last_update_timestamp
def get_jitter_peer_as_path_by_timestamp(asn, peer, ts, page_index, time_f, source):
    result = routing_path_dao.get_jitter_peer_as_path_by_timestamp(asn, ts, peer, time_f, source)
    count = result.count()
    result_as_path = []
    # c = 0
    for i in result.skip(int(page_index) * 1024).limit(1024):
        i["prefix"] = ipaddress.ip_network(i["prefix"])
        new_path_list = i['raws']
        last_t = ''

        if len(new_path_list) == 1 and 'A' in new_path_list[0]:
            result_as_path.append({'prefix': str(i["prefix"]), 'as_path': new_path_list, 'A': 1, 'W': 0, 'F': 0})
            continue
        o = {'prefix': str(i["prefix"]), 'as_path': [], 'A': 0, 'W': 0, 'F': 0}

        first = True
        no_match = False
        for as_path in new_path_list:

            if 'W' in as_path and no_match:
                no_match = False
                continue

            if 'W' in as_path and first and ('last-as-path' not in i or peer not in i['last-as-path']):
                continue

            if 'A' in as_path and peer not in as_path:
                no_match = True
                continue

            o[as_path.split('|')[2]] += 1
            if first:
                last_t = as_path[0]
            else:
                if last_t != as_path[0]:
                    o['F'] += 1
                    last_t = as_path[0]

            if 'W' in as_path and first:
                first = False
                o['as_path'].append([as_path, i['last-as-path']])
                continue

            o['as_path'].append(as_path)
            no_match = False
            if first:
                first = False

        if len(o['as_path']) != 0:
            result_as_path.append(o)

    return {
        'result_as_path': result_as_path,
        'total': count
    }


def get_jitter_top_n_tier1_by_as(asn, st, et, source):
    result = routing_path_dao.get_jitter_top_n_tier1_by_as(asn, st, et, source)
    _list = []
    for i in result:
        i['K'] = i['_id']
        i['V'] = i['F']
        del i['_id']
        del i['F']
        _list.append(i)
    return _list


def get_jitter_last_as_path_by_prefix(asn, peer, ts, prefix):
    ts = int(ts) / 1000
    print(ts - 300)
    # result = routing_path_dao.get_jitter_top_n_tier1_by_as(asn, st, et)
    return None


@record_last_update_timestamp
def get_FITI_jitter_topN_prefix_by_prefix(prefix, st, et, source):
    result = routing_path_dao.get_FITI_jitter_topN_prefix_by_prefix(prefix, st, et, source)
    _list = []
    for i in result:
        i['prefix'] = str(ipaddress.ip_network(i['_id'].strip('\n')))
        i['K'] = i['prefix']
        i['V'] = i['sum']
        del i['_id']
        _list.append(i)
    return _list


@record_last_update_timestamp
def get_FITI_jitter_data_by_prefix(p_prefix, prefix, st, et, source):
    ip, pfx = prefix.split('/')
    prefix = f'{ipaddress.ip_address(ip).exploded}/{pfx}'
    result = routing_path_dao.get_FITI_jitter_data_by_prefix(p_prefix, prefix, st, et, source)
    record = {}
    try:
        record = next(result)
    except Exception:
        pass
    record['A_list'].reverse()
    record['F_list'].reverse()
    record['W_list'].reverse()
    return record


@record_last_update_timestamp
def get_jitter_top_n_prefix_by_as_and_pfx(asn, pfx, st, et, source):
    result = routing_path_dao.get_jitter_top_n_prefix_by_as_and_pfx(asn, pfx, st, et, source)
    _list = []
    for i in result:
        i['prefix'] = str(ipaddress.ip_network(i['_id'].strip('\n')))
        i['K'] = i['prefix']
        i['V'] = i['sum']
        del i['_id']
        _list.append(i)
    return _list


@record_last_update_timestamp
def get_jitter_data_by_asn_and_prefix(asn, prefix, ppfx, st, et, source):
    ip, pfx = prefix.split('/')
    prefix = f'{ipaddress.ip_address(ip).exploded}/{pfx}'
    result = routing_path_dao.get_jitter_data_by_asn_and_prefix(asn, prefix, ppfx, st, et, source)
    record = {}
    try:
        record = next(result)
        # print(record)
    except Exception:
        pass
    record['A_list'].reverse()
    record['F_list'].reverse()
    record['W_list'].reverse()
    return record


@record_last_update_timestamp
def get_jitter_top_n_peer_by_as_and_pfx(asn, pfx, st, et, source):
    result = routing_path_dao.get_jitter_top_n_peer_by_as_and_pfx(asn, pfx, st, et, source)
    _list = []
    for i in result:
        i['K'] = i['_id']
        i['V'] = i['A']
        del i['_id']
        del i['A']
        _list.append(i)
    return _list


@record_last_update_timestamp
def get_jitter_data_by_peer_asn_and_pfx(asn, pfx, peer, st, et, source):
    result = routing_path_dao.get_jitter_data_by_peer_asn_and_pfx(asn, pfx, peer, st, et, source)
    try:
        record = next(result)
        del record['_id']
        return record
    except Exception as e:
        return {}
