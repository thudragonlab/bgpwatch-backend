from bson import ObjectId

from src.model import get_collection, event_collection_map
from utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)
db_name = 'fake-as-path'
type1_col = 'type1_event'
type2_col = 'type2_aggregated_event'


def get_data_by_timestamp_from_type1(st, et):
    collection = get_collection(db_name, type1_col)
    condition = {'timestamp': {'$gte': int(st), '$lte': int(et)}}
    return collection.find(condition).limit(1000)


def get_type2_record_by_id(_id):
    collection = get_collection(db_name, type2_col)
    return collection.find_one({'_id': ObjectId(_id)})


def get_data_by_timestamp_from_type2(st, et):
    collection = get_collection(db_name, type2_col)
    condition = {'timestamp': {'$gte': int(st), '$lte': int(et)}, "suspicious_link.2": {'$lt': 0.5}}
    return collection.find(condition).limit(5000)
