from src.model import get_date_of_data, get_daily_collection, get_col_from_mapping
from utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)


def get_date_of_date():
    return get_date_of_data('rtree-hash_info')
    # return conn['routing_tree_info']['hash_info_2023_02_17']


#
def get_hash_by_prefix(prefix):
    # rtree_info =
    return get_daily_collection('rtree-hash_info').find_one({'_id': prefix})
    # return conn['routing_tree_info']['hash_info_2023_02_17'].find_one({'_id': prefix})


def get_one_hash_by_condition(condition):
    # rtree_info =
    return get_daily_collection('rtree-hash_info').find_one(condition)
    # return conn['routing_tree_info']['hash_info_2023_02_17'].find_one({'_id': prefix})


def get_rtree_by_hash(_hash):
    col = get_daily_collection('rtree-tree_info')
    try:
        rtree_info = col.find_one({'_id': int(_hash)})
    except Exception as e:
        log.error(e)
        rtree_info = col.find_one({'_id': _hash})

    # rtree_info = conn['routing_tree_info']['tree_info_2023_03_27'].find_one({'_id': int(_hash)})
    return rtree_info


def get_route_by_prefix(final_regex):
    # return conn['routing_tree_info']['hash_info_2023_03_27'].find({'_id': {'$regex': final_regex}})
    col = get_daily_collection('rtree-hash_info')
    return col.find({'_id': {'$regex': final_regex}})


def get_route_by_condition(condition):
    col = get_daily_collection('rtree-hash_info')
    # return conn['routing_tree_info']['hash_info_2023_03_27'].find(condition)
    return col.find(condition)


def get_cluster_info_by_asn(asn):
    rtree_info = get_daily_collection('cluster_info').find_one({'_id': asn})
    # rtree_info = conn['routing_tree_info']['cluster_info_10_2023_02_17'].find_one({'_id': asn})

    return rtree_info


def get_matched_hash_by_rtree(rtree):
    if not rtree:
        return []

    Allroots = rtree['Allroots']
    nodes = rtree['nodes']
    aggregate_pipe = [
        {
            '$match': {
                'nodes': {
                    '$in': Allroots
                }
                ,
                'Allroots': {
                    '$nin': Allroots,
                    '$in': nodes
                }
                ,
                'ASroots': {
                    '$nin': Allroots,
                    '$in': nodes
                }
            }
        }
        , {
            '$group': {
                '_id': '$_id',
                'hash': {
                    '$push': '$_id'
                }
            }
        }
    ]
    return get_daily_collection('rtree-tree_info').aggregate(aggregate_pipe, allowDiskUse=True)


def get_jitter_top_n_prefix_by_as(asn, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000

    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')
    print(col.name)
    aggregate_pipelines = [
        {
            '$match':

            # query: The query in MQL.

                {
                    'timestamp': {
                        '$gte': int(st),
                        '$lte': int(et),
                    },
                    'asn': asn,
                    'flip': {'$gt': 1},
                    'source': source
                },
        },
        {
            '$project':

                {
                    'prefix': 1,
                    'filp_count': '$flip',
                },
        },
        {
            '$group':
            # /**
            #  * _id: The id of the group.
            #  * fieldN: The first field name.
            #  */
                {
                    '_id': "$prefix",
                    'sum': {
                        '$sum': "$filp_count",
                    },
                },
        },
        {
            '$sort':
            # /**
            #  * Provide any number of field/order pairs.
            #  */
                {
                    'sum': -1,
                },
        },
        {
            '$limit':
            # /**
            #  * Provide the number of documents to limit.
            #  */
                10,
        },
    ]

    return col.aggregate(aggregate_pipelines, allowDiskUse=True)


def get_jitter_data_by_prefix(asn, prefix, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000
    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')
    print(col.name)
    aggregate_pipelines = [
        {
            '$match':
            # /**
            #  * query: The query in MQL.
            #  */
                {
                    'prefix': prefix,
                    'asn': asn,
                    'timestamp': {
                        '$gte': int(st),
                        '$lte': int(et),
                    },

                    'source': source
                },
        },

        {
            '$project':
            #                           / **
            #                       * specifications: The
            # fields
            # to
            # * include or exclude.
            # * /
                {
                    'prefix': 1,
                    'timestamp': 1,
                    'raws': 1,
                    'A': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$A", False],
                            },

                            'then': "$A",

                            'else': 0,

                        },
                    },

                    'W': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$W", False],
                            },

                            'then': "$W",

                            'else': 0,

                        },
                    },
                    'F': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$flip", False],
                            },

                            'then': "$flip",

                            'else': 0,

                        },
                    },
                },
        },
        {
            '$project':
            # /**
            #  * specifications: The fields to
            #  *   include or exclude.
            #  */
                {
                    'prefix': 1,
                    'raws': 1,
                    'A': [{'$multiply': ["$timestamp", 1000]}, "$A"],
                    'W': [{'$multiply': ["$timestamp", 1000]}, "$W"],
                    'F': [{'$multiply': ["$timestamp", 1000]}, "$F"],
                },
        },
        # {
        #     '$group':
        #     # /**
        #     #  * _id: The id of the group.
        #     #  * fieldN: The first field name.
        #     #  */
        #         {
        #             '_id': "$prefix",
        #             'as_path_list': {
        #                 '$push': '$raws'
        #             },
        #             'A_list': {
        #                 '$push': "$A",
        #             },
        #             'W_list': {
        #                 '$push': "$W",
        #             },
        #             'F_list': {
        #                 '$push': "$F",
        #             },
        #         },
        # },
    ]
    # print(aggregate_pipelines)
    return col.aggregate(aggregate_pipelines, allowDiskUse=True,batchSize=1024)


def get_jitter_top_n_peer_by_as(asn, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000
    col = get_col_from_mapping('route-jitter-peer')
    print(col)
    aggregate_pipelines = [
        {
            '$match': {
                'timestamp': {
                    '$gte': int(st),
                    '$lte': int(et),
                },
                'asn': asn,

                'source': source
            }
        }, {
            '$group': {
                '_id': '$peer',
                'A': {
                    '$sum': '$A'
                },
            }
        }, {
            '$sort': {
                'A': -1
            }
        }, {
            '$limit':
            # /**
            #  * Provide the number of documents to limit.
            #  */
                10,
        },
    ]
    print(aggregate_pipelines)
    return col.aggregate(aggregate_pipelines)


def get_jitter_data_by_peer_asn(asn, peer, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000
    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')

    aggregate_pipelines = [
        {
            '$match': {
                'timestamp': {
                    '$gte': int(st),
                    '$lte': int(et),
                },
                'asn': asn,
                "as_path": {
                    "$elemMatch": {
                        "2": peer,
                    }
                },
                'source': source
            }
        },
        {
            '$unwind': {
                'path': '$as_path'
            }
        }, {
            '$match': {
                'as_path.2': peer
            }
        }, {
            '$group': {
                '_id': {
                    'prefix': '$prefix',
                    'ts': '$timestamp'
                },
                'F': {
                    '$sum': '$flip'
                },
                'W': {
                    '$sum': '$W'
                },
                'A': {
                    '$sum': 1
                },
                'C': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                'F': {
                    '$divide': [
                        '$F', '$C'
                    ]
                },
                'W': {
                    '$divide': [
                        '$W', '$C'
                    ]
                },
                'A': 1
            }
        }, {
            '$group': {
                '_id': '$_id.ts',
                'sum_A': {
                    '$sum': '$A'
                },
                'sum_W': {
                    '$sum': '$W'
                },
                'sum_F': {
                    '$sum': '$F'
                }
            }
        }, {
            '$project': {
                'A': [{'$multiply': ["$_id", 1000]}, "$sum_A"],
                'W': [{'$multiply': ["$_id", 1000]}, "$sum_W"],
                'F': [{'$multiply': ["$_id", 1000]}, "$sum_F"],
            }
        }, {
            '$group': {
                '_id': 'Result',
                'A_list': {
                    '$push': '$A'
                },
                'W_list': {
                    '$push': '$W'
                },
                'F_list': {
                    '$push': '$F'
                }
            }
        }
    ]
    return col.aggregate(aggregate_pipelines, allowDiskUse=True)


def get_jitter_peer_as_path_by_timestamp(asn, ts, peer, time_f, source="Tsinghua"):
    ts = int(ts) / 1000

    col = get_col_from_mapping('route-jitter' if '1' in time_f else 'route-jitter-hour')
    print(col.name)
    condition = {'timestamp': int(ts), 'asn': asn, "as_path": {
        "$elemMatch": {
            "2": peer,
        }
    },
                 'source': source}
    return col.find(condition).batch_size(1024)


def get_jitter_top_n_tier1_by_as(asn, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000

    col = get_col_from_mapping('route-jitter')
    aggregate_pipelines = [
        {
            '$match': {
                'timestamp': {
                    '$gte': int(st),
                    '$lte': int(et),
                },
                'asn': asn,
                'expired_date': {
                    '$exists': True
                },
                'flip': {
                    '$gt': 0
                },
                'source': source
            }
        }, {
            '$unwind': {
                'path': '$as_path'
            }
        }, {
            '$project': {
                'asn': 1,
                'A': 1,
                'W': 1,
                'flip': 1,
                'prefix': 1,
                'timestamp': 1,
                'tier1_as': {
                    '$split': [
                        '$as_path', ' '
                    ]
                }
            }
        }, {
            '$match': {
                '$nor': [
                    {
                        'tier1_as': {
                            '$exists': False
                        }
                    }, {
                        'tier1_as': {
                            '$size': 0
                        }
                    }, {
                        'tier1_as': {
                            '$size': 1
                        }
                    }
                ]
            }
        }, {
            '$project': {
                'asn': 1,
                'A': 1,
                'W': 1,
                'flip': 1,
                'prefix': 1,
                'timestamp': 1,
                'tier1_as': {
                    '$arrayElemAt': [
                        '$tier1_as', -1
                    ]
                }
            }
        }, {
            '$match': {
                'tier1_as': {
                    '$exists': True
                }
            }
        }, {
            '$group': {
                '_id': {
                    'prefix': '$prefix',
                    'ts': '$timestamp',
                    'tier1': '$tier1_as'
                },
                'F': {
                    '$sum': '$flip'
                },
                'count': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                'F': {
                    '$divide': [
                        '$F', '$count'
                    ]
                }
            }
        }, {
            '$group': {
                '_id': '$_id.tier1',
                'F': {
                    '$sum': '$F'
                }
            }
        }, {
            '$sort': {
                'F': -1
            }
        }, {
            '$limit': 10
        }
    ]
    return col.aggregate(aggregate_pipelines, allowDiskUse=True)


def find_last_as_path(ts, asn, prefix, source="Tsinghua"):
    col = get_col_from_mapping('route-jitter')
    ts = int(ts) / 1000
    condition = {'timestamp': {'$lt': int(ts)}, 'asn': asn, 'prefix': prefix, 'expired_date': {'$exists': True}, 'source': source}
    return col.find_one(condition)


def get_FITI_jitter_topN_prefix_by_prefix(prefix, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000

    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')
    print(col.name)
    aggregate_pipelines = [
        {
            '$match':

            # query: The query in MQL.

                {
                    'timestamp': {
                        '$gte': int(st),
                        '$lte': int(et),
                    },
                    'asn': '38272',
                    'peer_prefix': prefix,
                    'flip': {'$gt': 1}, 'source': source
                },
        },
        {
            '$project':

                {
                    'prefix': 1,
                    'filp_count': '$flip',
                },
        },
        {
            '$group':
            # /**
            #  * _id: The id of the group.
            #  * fieldN: The first field name.
            #  */
                {
                    '_id': "$prefix",
                    'sum': {
                        '$sum': "$filp_count",
                    },
                },
        },
        {
            '$sort':
            # /**
            #  * Provide any number of field/order pairs.
            #  */
                {
                    'sum': -1,
                },
        },
        {
            '$limit':
            # /**get_jitter_data_by_prefix
            #  * Provide the number of documents to limit.
            #  */
                10,
        },
    ]

    return col.aggregate(aggregate_pipelines, allowDiskUse=True)


def get_FITI_jitter_data_by_prefix(p_prefix, prefix, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000
    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')
    print(col.name)
    aggregate_pipelines = [
        {
            '$match':
            # /**
            #  * query: The query in MQL.
            #  */
                {
                    'prefix': prefix,
                    'peer_prefix': p_prefix,
                    'asn': '38272',
                    'timestamp': {
                        '$gte': int(st),
                        '$lte': int(et),
                    },
                    'source': source
                },
        },

        {
            '$project':
            #                           / **
            #                       * specifications: The
            # fields
            # to
            # * include or exclude.
            # * /
                {
                    'prefix': 1,
                    'timestamp': 1,
                    'raws': 1,
                    'A': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$A", False],
                            },

                            'then': "$A",

                            'else': 0,

                        },
                    },

                    'W': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$W", False],
                            },

                            'then': "$W",

                            'else': 0,

                        },
                    },
                    'F': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$flip", False],
                            },

                            'then': "$flip",

                            'else': 0,

                        },
                    },
                },
        },
        {
            '$project':
            # /**
            #  * specifications: The fields to
            #  *   include or exclude.
            #  */
                {
                    'prefix': 1,
                    'raws': 1,
                    'A': [{'$multiply': ["$timestamp", 1000]}, "$A"],
                    'W': [{'$multiply': ["$timestamp", 1000]}, "$W"],
                    'F': [{'$multiply': ["$timestamp", 1000]}, "$F"],
                },
        },
        {
            '$group':
            # /**
            #  * _id: The id of the group.
            #  * fieldN: The first field name.
            #  */
                {
                    '_id': "$prefix",
                    'as_path_list': {
                        '$push': '$raws'
                    },
                    'A_list': {
                        '$push': "$A",
                    },
                    'W_list': {
                        '$push': "$W",
                    },
                    'F_list': {
                        '$push': "$F",
                    },
                },
        },
    ]
    # print(aggregate_pipelines)
    return col.aggregate(aggregate_pipelines, allowDiskUse=True)


def get_jitter_top_n_prefix_by_as_and_pfx(asn, pfx, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000

    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')
    print(col.name)
    aggregate_pipelines = [
        {
            '$match':

            # query: The query in MQL.

                {
                    'timestamp': {
                        '$gte': int(st),
                        '$lte': int(et),
                    },
                    'asn': asn,
                    'flip': {'$gt': 1},
                    'source': source,
                    'peer_prefix': pfx,
                },
        },
        {
            '$project':

                {
                    'prefix': 1,
                    'filp_count': '$flip',
                },
        },
        {
            '$group':
            # /**
            #  * _id: The id of the group.
            #  * fieldN: The first field name.
            #  */
                {
                    '_id': "$prefix",
                    'sum': {
                        '$sum': "$filp_count",
                    },
                },
        },
        {
            '$sort':
            # /**
            #  * Provide any number of field/order pairs.
            #  */
                {
                    'sum': -1,
                },
        },
        {
            '$limit':
            # /**
            #  * Provide the number of documents to limit.
            #  */
                10,
        },
    ]

    return col.aggregate(aggregate_pipelines, allowDiskUse=True)


def get_jitter_data_by_asn_and_prefix(asn, prefix, ppfx, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000
    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')
    print(col.name)
    aggregate_pipelines = [
        {
            '$match':
            # /**
            #  * query: The query in MQL.
            #  */
                {
                    'prefix': prefix,
                    'asn': asn,
                    'timestamp': {
                        '$gte': int(st),
                        '$lte': int(et),
                    },
                    'peer_prefix': ppfx,
                    'source': source
                },
        },

        {
            '$project':
            #                           / **
            #                       * specifications: The
            # fields
            # to
            # * include or exclude.
            # * /
                {
                    'prefix': 1,
                    'timestamp': 1,
                    'raws': 1,
                    'A': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$A", False],
                            },

                            'then': "$A",

                            'else': 0,

                        },
                    },

                    'W': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$W", False],
                            },

                            'then': "$W",

                            'else': 0,

                        },
                    },
                    'F': {
                        '$cond': {
                            'if': {
                                '$ifNull': ["$flip", False],
                            },

                            'then': "$flip",

                            'else': 0,

                        },
                    },
                },
        },
        {
            '$project':
            # /**
            #  * specifications: The fields to
            #  *   include or exclude.
            #  */
                {
                    'prefix': 1,
                    'raws': 1,
                    'A': [{'$multiply': ["$timestamp", 1000]}, "$A"],
                    'W': [{'$multiply': ["$timestamp", 1000]}, "$W"],
                    'F': [{'$multiply': ["$timestamp", 1000]}, "$F"],
                },
        },
        {
            '$group':
            # /**
            #  * _id: The id of the group.
            #  * fieldN: The first field name.
            #  */
                {
                    '_id': "$prefix",
                    'as_path_list': {
                        '$push': '$raws'
                    },
                    'A_list': {
                        '$push': "$A",
                    },
                    'W_list': {
                        '$push': "$W",
                    },
                    'F_list': {
                        '$push': "$F",
                    },
                },
        },
    ]
    # print(aggregate_pipelines)
    return col.aggregate(aggregate_pipelines, allowDiskUse=True)


def get_jitter_top_n_peer_by_as_and_pfx(asn, pfx, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000
    col = get_col_from_mapping('route-jitter-peer')
    print(col)
    aggregate_pipelines = [
        {
            '$match': {
                'timestamp': {
                    '$gte': int(st),
                    '$lte': int(et),
                },
                'asn': asn,
                'peer_prefix': pfx,
                'source': source
            }
        }, {
            '$group': {
                '_id': '$peer',
                'A': {
                    '$sum': '$A'
                },
            }
        }, {
            '$sort': {
                'A': -1
            }
        }, {
            '$limit':
            # /**
            #  * Provide the number of documents to limit.
            #  */
                10,
        },
    ]
    print(aggregate_pipelines)
    return col.aggregate(aggregate_pipelines)


def get_jitter_data_by_peer_asn_and_pfx(asn, pfx, peer, st, et, source="Tsinghua"):
    st = int(st) / 1000
    et = int(et) / 1000
    col = get_col_from_mapping('route-jitter' if et - st <= 86400 else 'route-jitter-hour')

    aggregate_pipelines = [
        {
            '$match': {
                'timestamp': {
                    '$gte': int(st),
                    '$lte': int(et),
                },
                'asn': asn,
                "as_path": {
                    "$elemMatch": {
                        "2": peer,
                    }
                },
                'peer_prefix': pfx,
                'source': source
            }
        },
        {
            '$unwind': {
                'path': '$as_path'
            }
        }, {
            '$match': {
                'as_path.2': peer
            }
        }, {
            '$group': {
                '_id': {
                    'prefix': '$prefix',
                    'ts': '$timestamp'
                },
                'F': {
                    '$sum': '$flip'
                },
                'W': {
                    '$sum': '$W'
                },
                'A': {
                    '$sum': 1
                },
                'C': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                'F': {
                    '$divide': [
                        '$F', '$C'
                    ]
                },
                'W': {
                    '$divide': [
                        '$W', '$C'
                    ]
                },
                'A': 1
            }
        }, {
            '$group': {
                '_id': '$_id.ts',
                'sum_A': {
                    '$sum': '$A'
                },
                'sum_W': {
                    '$sum': '$W'
                },
                'sum_F': {
                    '$sum': '$F'
                }
            }
        }, {
            '$project': {
                'A': [{'$multiply': ["$_id", 1000]}, "$sum_A"],
                'W': [{'$multiply': ["$_id", 1000]}, "$sum_W"],
                'F': [{'$multiply': ["$_id", 1000]}, "$sum_F"],
            }
        }, {
            '$group': {
                '_id': 'Result',
                'A_list': {
                    '$push': '$A'
                },
                'W_list': {
                    '$push': '$W'
                },
                'F_list': {
                    '$push': '$F'
                }
            }
        }
    ]
    print(aggregate_pipelines)
    return col.aggregate(aggregate_pipelines, allowDiskUse=True)
