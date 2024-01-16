from src.model import get_collection, event_collection_map
from src.utils.logger import get_logger, APP_LOG_NAME
log = get_logger(APP_LOG_NAME)

def get_hijack_collection_by_type(_type):
    return get_collection('hijack-2022', event_collection_map[_type])


def get_hijack_count_by_date(start, end, _type):
    return get_hijack_collection_by_type(_type).count({'start_timestamp': {'$gt': start,'$lt': end},'duration': {'$not': {'$regex': '-'}}})


def get_hijack_event_by_date(start, end, _type):
    return get_hijack_collection_by_type(_type).find({'start_timestamp': {'$gt': start,'$lt': end}}, {
        'level': 1,
        'victim_as': 1,
        'victim_as_description': 1,
        'victim_as_country': 1,
        'hijack_as': 1,
        'hijack_as_description': 1,
        'hijack_as_country': 1,
        'prefix_list': 1,
        'prefix': 1,
        'start_datetime': 1,
        'end_datetime': 1,
        'duration': 1
    })


def projective_hijack_by_date(start, end, _type):
    condition = [
        {
            '$match': {'start_timestamp': {'$gt': start,'$lt': end},'duration': {'$not': {'$regex': '-'}}}
        },
        {
            '$project': {
                '_id': 1,
                'suspicious_as': 1,
                'before_as': 1,
                'suspicious_as_country': 1,
                'before_as_country': 1,
                'prefix': 1,
                'start_timestamp': {"$multiply": [{'$subtract': ['$start_timestamp', {'$mod': ['$start_timestamp', 86400]}]}, 1000]},
                'end_timestamp': {"$multiply": [{'$subtract': ['$end_timestamp', {'$mod': ['$end_timestamp', 86400]}]}, 1000]},
            }
        }
    ]
    # if 'Ongoing' in _type:
    #     condition.append({
    #         '$limit':99
    #     })
    return get_hijack_collection_by_type(_type).aggregate(condition)


def get_hijack_by_date(start, end, _type):
    return get_hijack_collection_by_type(_type).aggregate([
        {
            '$match': {'start_timestamp': {'$gt': start, '$lt': end}}
        },
        {
            '$project': {
                '_id': 1,
                'suspicious_as': 1,
                'before_as': 1,
                'suspicious_as_country': 1,
                'before_as_country': 1,
                'prefix': 1,
                'start_timestamp': {"$multiply": ['$start_timestamp', 1000]},
                # 'end_timestamp': {"$multiply": ['$end_timestamp', 1000]},
            }
        }
    ])
