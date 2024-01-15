from src.model import *
from bson import ObjectId
from utils.logger import get_logger, APP_LOG_NAME
import base64

log = get_logger(APP_LOG_NAME)


def register(user_name, password, email, token, _id):
    count = user_collection.count_documents({'user_name': user_name})
    if count:
        return 'Duplicate Username'

    user_collection.insert_one({
        '_id': ObjectId(_id),
        'user_name': user_name,
        'password': base64.b64encode(bytes(password, 'utf-8')),
        'email': email,
        'create_ts':datetime.utcnow().timestamp(),
        'token': token,
    })

    return {
        '_id': _id,
        'user_name': user_name,
        'token': token,
        'email': email,
    }


def login(user_name, password):
    result = user_collection.find_one(
        {'user_name': user_name, '$or': [{'password': base64.b64encode(bytes(password, 'utf-8'))}, {'password': password}]})

    if result:
        return {
            'user_name': user_name,
            'token': str(result['token']),
            'email': str(result['email']),
            '_id': str(result['_id'])
        }

    return 'Not Found'


def find_user_by_name(user_name):
    condition = {'user_name': user_name}
    return user_collection.find_one(condition)


def verify_email(user_name):
    count = user_collection.count_documents({'user_name': user_name})
    if count:
        return False
    return True


def add_as_with_list(_id, as_list, _user_info):
    email = _user_info['email']
    update_count = user_collection.update({'_id': ObjectId(_id)}, {'$addToSet': {'subscribed_as': {'$each': as_list}}})
    subscribe_as_col = get_collection('bgp-user', 'subscribed-as-email')

    for _as in as_list:
        subscribe_as_col.find_and_modify({'_id': str(_as)}, {'$addToSet': {'email_list': email}}, upsert=True)
    if update_count['n']:
        return True
    else:
        return False


def del_as_in_list(_id, as_list):
    update_count = user_collection.update({'_id': ObjectId(_id)}, {'$pull': {'subscribed_as': {'$in': as_list}}})
    log.debug(update_count)
    if update_count['n']:
        return True
    else:
        return False


def get_user_subscribe_list(_id):
    user_info = user_collection.find_one({'_id': ObjectId(_id)}, {'subscribed_as': 1})
    return user_info


def get_user_subscribed_as_prefix(_id):
    user_info = user_collection.find_one({'_id': ObjectId(_id)}, {'subscribed_as_prefix': 1})
    return user_info


def update_pwd(user, pwd):
    condition_list = [{'user_name': user}, {"$set": {'password': base64.b64encode(bytes(pwd, 'utf-8'))}}]
    count = user_collection.update_one(*condition_list)
    print(*condition_list)
    print(count.matched_count)
    return count


def add_prefix_subscribe(_id, asn, prefix):
    update_count = user_collection.update({'_id': ObjectId(_id)}, {'$addToSet': {f'subscribed_as_prefix.{asn}': prefix}})
    if update_count['n']:
        return True
    else:
        return False


def del_prefix_in_prefix_list(_id, asn, prefix):
    update_count = user_collection.update({'_id': ObjectId(_id)}, {'$pull': {f'subscribed_as_prefix.{asn}': prefix}})
    if update_count['n']:
        return True
    else:
        return False


def del_asn_in_prefix_list(_id, asn):
    update_count = user_collection.update({'_id': ObjectId(_id)}, {'$unset': {f'subscribed_as_prefix.{asn}': ''}})
    if update_count['n']:
        return True
    else:
        return False


def add_source_ip(source, _id):
    update_count = user_collection.update({'_id': ObjectId(_id)}, {'$addToSet': {f'source-ips': source}})
    if update_count['n']:
        return True
    else:
        return False


def get_source_ips(_id):
    return user_collection.find_one({'_id': ObjectId(_id)}, {f'source-ips': 1})


def del_source_ip(ip_addr, _id):
    update_count = user_collection.update({'_id': ObjectId(_id)}, {'$pull': {f'source-ips': ip_addr}})
    print(update_count)
    if update_count['nModified']:
        return True
    else:
        return False