import ipaddress
from typing import List

from bson import ObjectId
import jwt
import requests
from flask import request
from src.model import last_update_timestamp_map

SALT = 'dragonLab_TSU'

header = {
    'typ': 'jwt',
    'alg': 'HS256'
}


def create_token(username, pwd, email):
    payload = {
        'user_id': 1,
        'username': username,
        'pwd': pwd,
        'email': email,
        '_id': ObjectId().__str__()
        # 'exp': datetime.utcnow() + timedelta(seconds=5)
    }

    result = jwt.encode(payload=payload, key=SALT, algorithm='HS256', headers=header)

    return result


def encode(payload):
    result = jwt.encode(payload=payload, key=SALT, algorithm='HS256', headers=header)
    return result


def parse_token(token):
    # print()

    result = jwt.decode(jwt=token, key=SALT, algorithms='HS256', headers=header, options={'verify_exp': False})
    return result


def generate_subnet_regex(prefix: str) -> str:
    ip, prefix = prefix.split('/')
    return f'^{ip_to_binary(ipaddress.ip_address(ip).exploded)[:int(prefix)]}'


def generate_supernet_regex(prefix: str) -> List[str]:
    addr = ipaddress.ip_network(prefix)
    _list = []
    for i in range(0, addr.prefixlen + 1 - 8):
        _list.append(addr.supernet(i).exploded)
    return _list


def sendMsgToSlack(json):
    return requests.post('https://hooks.slack.com/services/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',
                         json=json)


def ip_to_binary(ip_address):
    # 如果是IPv4地址
    if '.' in ip_address:
        # 将IPv4地址转换为32位二进制
        binary_ip = bin(int(''.join(['{:08b}'.format(int(octet)) for octet in ip_address.split('.')]), 2))[2:]
        # 补全32位
        binary_ip = '0' * (32 - len(binary_ip)) + binary_ip
    # 如果是IPv6地址
    else:

        # 将IPv6地址转换为128位二进制
        binary_ip = bin(int(''.join(['{:04x}'.format(int(octet, 16)) for octet in ip_address.split(':')]), 16))[2:]
        # 补全128位
        binary_ip = '0' * (128 - len(binary_ip)) + binary_ip
    return binary_ip


def record_last_update_timestamp(handler):
    def wrapper(*args, **kwargs):
        data = handler(*args, **kwargs)
        key = f'{request.path}{request.url.split("/", 3)[3]}'
        res = {'data': data, 'status': True}
        if key in last_update_timestamp_map:
            res['lastUpdateTimeStamp'] = last_update_timestamp_map[key]
            del last_update_timestamp_map[key]
        if 'status' in data:
            res['status'] = data['status']
        if 'statusCode' in data:
            res['statusCode'] = data['statusCode']
        if 'message' in data:
            res['statusCode'] = data['message']
        if 'msg' in data:
            res['statusCode'] = data['msg']

        return res

    return wrapper


def get_regex_by_ip(ip_address):
    if ':' not in ip_address:
        if '/' not in ip_address:
            input_list = [ip_address, '32']
        else:
            input_list = ip_address.split('/')

    else:
        if '/' not in ip_address:
            input_list = [ip_address, '128']
        else:
            input_list = ip_address.split('/')
    condition = {
        '$or': [],
        '$and': [{'Hash': {'$ne': '-1'}}, {'Hash': {'$ne': -1}}],
    }
    condition['$or'].append({'binary': {'$regex': f'{generate_subnet_regex("/".join(input_list))}'}})
    condition['$or'].append({'_id': {'$in': generate_supernet_regex("/".join(input_list))}})
    return condition, input_list


def ip_to_ipbinary(prefix):
    # 如果是IPv4地址
    ip_address,p = prefix.split('/')
    if '.' in ip_address:
        # 将IPv4地址转换为32位二进制
        binary_ip = bin(int(''.join(['{:08b}'.format(int(octet)) for octet in ip_address.split('.')]), 2))[2:]
        # 补全32位
        binary_ip = '4|'+'0' * (32 - len(binary_ip)) + binary_ip
    # 如果是IPv6地址
    else:
        # 将IPv6地址转换为128位二进制
        binary_ip = bin(int(''.join(['{:04x}'.format(int(octet, 16)) for octet in ip_address.split(':')]), 16))[2:]
        # 补全128位
        binary_ip = '6|'+'0' * (128 - len(binary_ip)) + binary_ip
    return binary_ip