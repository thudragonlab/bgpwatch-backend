from bson import ObjectId
from datetime import datetime
from src.model import get_collection, event_collection_map, get_daily_db, get_today_collection, get_col_from_mapping
from utils.logger import get_logger, APP_LOG_NAME
from hashlib import md5

log = get_logger(APP_LOG_NAME)
db_name = 'hijack-2022'


def get_events(st, et, event_type):
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    if 'SubMoas' in event_type:
        condition = {'start_timestamp': {'$gte': int(st), '$lte': int(et)}, 'is_subhijack': False, 'duration': {'$not': {'$regex': '-'}}}
        data = hijack_db.find(condition)
    elif 'Moas' in event_type:
        condition = {'start_timestamp': {'$gte': int(st), '$lte': int(et)}, 'is_hijack': False, 'duration': {'$not': {'$regex': '-'}}}
        data = hijack_db.find(condition)
    else:
        condition = {'start_timestamp': {'$gte': int(st), '$lte': int(et)}, 'duration': {'$not': {'$regex': '-'}}}
        data = hijack_db.find(condition)
    # if et - st > 3600 * 24 * 30 * 3:
    #     data = data.limit(999)

    return data


def find(condition, event_type):
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    data = hijack_db.find(condition).limit(99)
    return data


def get_event_detail(event_param):
    log.debug(f'{event_param}')
    event_id_list = event_param.split('|')
    if len(event_id_list) == 1:
        return None
    event_id = event_id_list[0].replace('_', '/')
    collection_name = event_id_list[1]
    if collection_name not in event_collection_map:
        return None
    _type = collection_name

    hijack_db = get_collection(db_name, event_collection_map[collection_name])

    try:
        log.debug(f'{event_param}')
        condition = {'$or':[{'event_id': event_id},{'event_id_list': event_id}]}
        print(condition)
        data = hijack_db.find_one(condition)
        if not data and 'Ongoing ' in collection_name:
            hijack_db = get_collection(db_name, event_collection_map[collection_name[8:]])
            _type = collection_name[8:]
            data = hijack_db.find_one(condition)

        if not data:
            # moas_col_name = 'Ongoing Moas'
            if 'Sub' in collection_name:
                moas_col_name = 'Ongoing SubMoas'
                event_id = event_id.replace('sub', 'submoas')
                condition = {'$or': [{'event_id': event_id}, {'event_id_list': event_id}]}
                if 'Ongoing ' in collection_name:
                    hijack_db = get_collection(db_name, event_collection_map[moas_col_name])
                    _type = moas_col_name
                    data = hijack_db.find_one(condition)
                if not data:
                    hijack_db = get_collection(db_name, event_collection_map[moas_col_name[8:]])
                    _type = moas_col_name[8:]
                    data = hijack_db.find_one(condition)
            else:
                moas_col_name = 'Ongoing Moas'
                event_id = event_id.replace('hijack', 'moas')
                condition = {'$or': [{'event_id': event_id}, {'event_id_list': event_id}]}
                if 'Ongoing ' in collection_name:
                    hijack_db = get_collection(db_name, event_collection_map[moas_col_name])
                    _type = moas_col_name
                    data = hijack_db.find_one(condition)
                if not data:
                    hijack_db = get_collection(db_name, event_collection_map[moas_col_name[8:]])
                    _type = moas_col_name[8:]
                    data = hijack_db.find_one(condition)

        return data,_type
    except Exception as e:
        print('Exception:%s' % e)
        return None,None


def update_confirm(_id, user_id, user, event_type, description='-'):
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    log_obj = {'user': user, 'accept/reject': 'accept', 'description': description, 'date': datetime.now().timestamp() * 1000, 'comments_list': []}
    u = hijack_db.update_one({"_id": ObjectId(_id)}, [{'$addFields': {f'logging.{user_id}': log_obj}}])
    return u.modified_count


def update_reject(_id, user_id, user, reason, event_type):
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    log_obj = {'user': user, 'accept/reject': 'reject', 'description': reason, 'date': datetime.now().timestamp() * 1000, 'comments_list': []}
    u = hijack_db.update_one({"_id": ObjectId(_id)}, [{'$addFields': {f'logging.{user_id}': log_obj}}])
    return u.modified_count


def update_unconfirmed(_id, user_id, event_type):
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    u = hijack_db.update_one({"_id": ObjectId(_id)}, {'$unset': {f'logging.{user_id}': ''}})
    return u.modified_count


def un_reject_event(_id, user_id, event_type):
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    u = hijack_db.update_one({"_id": ObjectId(_id)}, {'$unset': {f'logging.{user_id}': ''}})
    return u.modified_count


def add_sub_comment(_id, parent_user_id, user, event_type, comment, reply_user):
    user_id = user['_id']
    user_name = user['username']
    comment_id = md5(comment.encode('utf-8')).hexdigest()
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    comment_obj = {'_id': comment_id, 'comment': comment, 'user_name': user_name, 'user_id': user_id, 'date': datetime.now().timestamp() * 1000}
    if reply_user:
        comment_obj['reply_user'] = reply_user
    u = hijack_db.update_one({"_id": ObjectId(_id)}, {'$push': {f'logging.{parent_user_id}.comments_list': comment_obj}})
    return u.modified_count, comment_id


def del_sub_comment(_id, parent_user_id, event_type, comment_id):
    hijack_db = get_collection(db_name, event_collection_map[event_type])
    print({"_id": ObjectId(_id)}, {'$pop': {f'logging.{parent_user_id}.comments_list': {'_id': comment_id}}})
    u = hijack_db.update_one({"_id": ObjectId(_id)}, {'$pull': {f'logging.{parent_user_id}.comments_list': {'_id': comment_id}}})
    return u.modified_count


def get_events_by_condition(hijack_type, condition):
    hijack_db = get_collection(db_name, event_collection_map[hijack_type])
    return hijack_db.find(condition).sort([('start_timestamp', -1)]).limit(1000)


def get_event_detail_by_api(hijack_type, event_id):
    hijack_db = get_collection(db_name, event_collection_map[hijack_type])
    return hijack_db.find_one({'_id': ObjectId(event_id)})


def get_prefix_roa_history(binary_prefix):
    col = get_col_from_mapping('roa-db')
    result = col.find({'binary_prefix': {'$in': binary_prefix}, 'timestamp': {'$gte': datetime.utcnow().timestamp() - 86400}})
    return result
