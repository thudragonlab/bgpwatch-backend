from src.model import *


# @DeprecationWarning
# def get_providers_4538_model():
#     return as_route.aggregate([
#         # {
#         #     '$match':{'_id':'5.188.88.0/22'}
#         #
#         #     },
#         {
#             '$project': {
#                 "_id": "$_id",
#                 "split": {'$split': ["$data", "|"]}
#             }
#
#         },
#         {
#             '$project': {
#                 "_id": "$_id",
#                 'path': {'$split': [{
#                     '$arrayElemAt': ["$split", 6]
#                 }, ' ']},
#                 'asn': {
#                     '$arrayElemAt': ["$split", 4]
#                 },
#             }
#         },
#         {'$limit': 1000}
#     ])


def find_by_key_from_mongo(key):
    return get_daily_collection('serial1').find_one({'_id': key})


def get_providers_update_by_influx_db():
    update_list = []
    # for table in bgp_updates_4538:
    #     for row in table.records:
    #         if row.values['_value'] is None:
    #             continue
    #         path = row.values['_value']
    #         update_list.append(path[1:-1].split(','))
    return update_list


def get_prefixes_in_as_list(as_list):
    col = get_daily_collection('prefix_list')
    print(col.estimated_document_count())
    return get_daily_collection('prefix_list').find({'_id': {'$in': as_list}})


def get_as_info_by_list_from_db(asn_list):
    condition = {'_id': {'$in': [str(i) for i in asn_list]}}
    print(condition)
    return get_daily_collection('as_info').find(condition)


def get_country_distribute(asn_list):
    return get_daily_collection('as_info').aggregate([
        {
            '$match': {'_id': {'$in': asn_list}}
        },
        {
            '$group': {
                '_id': '$country.iso',
                'sum': {'$sum': 1}
            }
        }, {
            '$sort': {'sum': -1}
        }
    ], allowDiskUse=True)


def get_asinfo_from_db(asn):
    return get_daily_collection('dev-daily-as-route').find_one({'_id': asn})
    # return conn['dev-daily-as-route']['as-route-daily-20220601'].find_one({'_id': asn})


def get_real_time_data_from_period():
    real_time_data = []
    # bgp_updates_cernet_in_a_period = query_api.query('from(bucket:"bgp-updates-cernet") |> range(start: -30m)')
    # for table in bgp_updates_cernet_in_a_period:
    #     for row in table.records:
    #         real_time_data.append(row)
    return real_time_data


def get_real_time_data_limit_last_3600():
    real_time_data = []
    # bgp_updates_cernet_in_a_period = query_api.query(
    #     'from(bucket:"bgp-updates-cernet")'
    #     '|> range(start: -12h)'
    #     '|> sort(columns: ["_time"], desc: true)'
    #     '|> limit(n:3600)'
    # )
    # for table in bgp_updates_cernet_in_a_period:
    #     for row in table.records:
    #         real_time_data.append(row)
    return real_time_data


def get_real_time_data_by_second():
    real_time_data = []

    # bgp_updates_cernet_for_second = query_api.query('from(bucket:"bgp-updates-cernet") |> range(start: -1s)')
    # for table in bgp_updates_cernet_for_second:
    #     for row in table.records:
    #         real_time_data.append(row)
    return real_time_data


def get_as_list_by(asn):
    return get_daily_collection('serial1').find_one({'_id': asn})


def get_as_path_by_prefix(prefix, asn):
    aggregate_pipeLine = [
        {
            '$match': {'firstAs': asn, 'prefix': {'$regex': prefix}},
        },
        {
            '$limit': 100
        },
        {
            '$group': {'_id': '$path',
                       'prefixes': {'$push': '$prefix'}
                       },
        }
    ]
    # print(aggregate_pipeLine)
    table = get_daily_collection('cgtf_route_path')
    # print(table.name)
    return table.aggregate(aggregate_pipeLine)


def get_prefix_total_by_asn(asn):
    return get_daily_collection('cgtf_route_path').count_documents({'firstAs': asn})


#
# def get_hash_by_prefix(prefix):
#     # return get_daily_collection('rtree-hash_info').find_one({'_id': prefix})
#     return conn['routing_tree_info']['hash_info_2023_02_17'].find_one({'_id': prefix})
#
#
#
# def get_rtree_by_hash(_hash):
#     rtree_info = conn['routing_tree_info']['tree_info_2023_02_17'].find_one({'_id': _hash})
#     # rtree_info = get_daily_collection('rtree-tree_info')
#     # rtree_info = get_daily_collection('rtree-tree_info').find_one({'_id': _hash})
#     return rtree_info


def get_as_info(asn, as_name, org_name):
    col = get_daily_collection('as_info')

    find_condition = {}
    if asn:
        find_condition['_id'] = asn
    if as_name:
        find_condition['asnName'] = {'$regex': f'{as_name.upper()}|{as_name.lower()}'}
    if org_name:
        find_condition['$or'] = [{'asnName': {'$regex': org_name}}, {'as-org.org_name': {'$regex': org_name}},
                                 {'organization.orgName': {'$regex': org_name}}]
    print(find_condition)
    return col.find(find_condition).limit(200).sort([('_id', 1)])


def get_as_diff(subscribed_as):
    col = get_daily_collection('route_diff_summary')
    result = col.find({'_id': {'$in': subscribed_as}})

    static_list = []
    for i in result:
        static_list.append(i)
    db_id_list = list(map(lambda x: x['_id'], static_list))

    for _as in subscribed_as:
        if _as not in db_id_list:
            static_list.append({'_id': _as})
    return static_list


def get_as_path_by_condition(condition):
    aggregate_pipeLine = [
        {
            '$match': condition,
        },
        {
            '$limit': 100
        },
        {
            '$group': {'_id': '$path',
                       'prefixes': {'$push': '$prefix'}
                       },
        }
    ]
    # print(aggregate_pipeLine)
    table = get_daily_collection('cgtf_route_path')
    return table.aggregate(aggregate_pipeLine)


def get_cc2as_by_cc(cc):
    as_info_col = get_daily_collection('as_info')
    result = as_info_col.find({'country.iso': cc})
    return result


def get_as_relationship_by_as_list(as_list):
    serial1 = get_daily_collection('serial1')
    result = serial1.find({'_id': {'$in': as_list}}, {'peer-ases': 1, 'customer-ases': 1})
    return result


def get_diff_prefix_in_prefix_list(prefix_list):
    today_hash = get_daily_collection('rtree-hash_info')
    yesterday_hash = get_daily_collection('rtree-hash_info', 1)
    print(today_hash.name, yesterday_hash.name)
    result = today_hash.aggregate([
        {
            '$match': {
                '_id': {
                    '$in': prefix_list
                }
            }
        }
        , {
            '$lookup': {
                'from': yesterday_hash.name,
                'localField': '_id',
                'foreignField': '_id',
                'as': 'result'
            }
        }, {
            '$project': {
                '_id': 1,
                'Hash': 1,
                'LastHash': {
                    '$arrayElemAt': [
                        '$result.Hash', 0
                    ]
                }
            }
        }, {
            '$match': {
                '$expr': {
                    '$ne': [
                        '$Hash', '$LastHash'
                    ]
                }
            }
        }
    ])
    return result


def get_as_info_by_list_from_whois(asn_list):
    col = get_daily_collection('irr_WHOIS')
    return col.find({'aut-num': {'$in': list(map(lambda x: f'AS{x}', asn_list))}})
