import ipaddress

import src.model.user_dao as user_dao
import random
from src.service.util import record_last_update_timestamp, parse_token, SALT, create_token
import base64
import re

from src.utils.logger import INTERVAL_LOG_NAME, get_logger


@record_last_update_timestamp
def register_service(token):
    user_register_info = parse_token(token)
    user_name = user_register_info['username']
    password = user_register_info['pwd']
    email = user_register_info['email']
    _id = user_register_info['_id']
    data = user_dao.register(user_name, password, email, token, _id)

    status = 'success'

    if isinstance(data, str):
        status = False

    result = {'status': status, 'data': data}
    return result


@record_last_update_timestamp
def login_service(user_name, password):
    status = 'success'
    data = user_dao.login(user_name, password)

    if isinstance(data, str):
        status = False

    result = {'status': status, 'data': data, 'message': 'Login fail, Please check your username and password'}
    return result


@record_last_update_timestamp
def verify_email(user_name, password, email, host):
    email_regex = "^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
    verify_email = re.match(email_regex, email)
    if not verify_email:
        return {
            'status': False,
            'data': 'invalid Email'
        }

    data = user_dao.verify_email(user_name)

    if not data:
        return {
            'status': False,
            'data': 'Duplicate Username'
        }
    token = create_token(user_name, password, email)

    if isinstance(token, str):
        token = bytes(token, encoding='utf8')

    # http: // localhost: 8080 /  # /VerifyAccount?token=eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InB6ZDIyMSIsInB3ZCI6IjEyMyIsImVtYWlsIjoicGVpemlkb25nQHRzaW5naHVhLmVkdS5jbiJ9.S-5q4_6GyzgWX-S8Pgn148YZyzv1aqYZ3piPVY8A7mw
    url = '%s/#/VerifyAccount?token=%s' % (host, token.decode('utf-8'))
    send_email(email, 'please use this link to verify your email %s' % url, 'Verify Account')
    return {}

    # result = {'status': status, 'data': data}
    # return result


def send_email(receivers, content, title, type='plain'):
    import smtplib
    from email.mime.text import MIMEText
    # 设置服务器所需信息
    # 163邮箱服务器地址
    mail_host = 'smtphz.qiye.163.com'
    # mail_host = 'mail-m118112.qiye.163.com'

    # 163用户名
    mail_user = 'sec@cgtf.net'
    # 密码(部分邮箱为授权码)
    mail_pass = 'KxCUH75NZSHYFPPk'
    # 邮件发送方邮箱地址
    # sender = 'sec@cgtf.net'
    sender = 'sec@cgtf.net'
    # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    # receivers = 'peizidong@tsinghua.edu.cn'

    # 设置email信息
    # 邮件内容设置
    message = MIMEText(content, type, 'utf-8')
    # 邮件主题
    message['Subject'] = title
    # 发送方信息
    message['From'] = f'\"CGTF SEC\" <{sender}>'
    # 接受方信息
    if isinstance(receivers, list):
        message['To'] = ', '.join(receivers)
    else:
        message['To'] = receivers

    # 登录并发送邮件
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host)
        # 连接到服务器
        smtpObj.connect(mail_host, 465)
        # 登录到服务器
        smtpObj.login(mail_user, mail_pass)
        # 发送
        smtpObj.sendmail(
            sender, receivers, message.as_string())

        # 退出
        smtpObj.quit()
        log = get_logger(INTERVAL_LOG_NAME)
        log.debug('send message to %s success' % receivers)
    except smtplib.SMTPException as e:
        print('error', e)  # 打印错误


@record_last_update_timestamp
def forget(user_name, host):
    user = user_dao.find_user_by_name(user_name)
    if not user:
        return {'message': 'Not found user'}
    email = user['email']

    pos = random.randint(0, user_name.__len__())
    url = f'{host}#/updatePassword?user={base64.b64encode((user_name[:pos] + SALT + user_name[pos:]).encode()).decode()}'
    print(url)
    send_email(email, 'please use this link to update Your password %s' % url, 'Update password')
    return {'message': f'Please checkout you email {email}'}


@record_last_update_timestamp
def updatePwd(user_name, pwd):
    user = user_dao.find_user_by_name(user_name)
    if not user:
        return {'message': 'Not found user'}
    count = user_dao.update_pwd(user_name, pwd)
    if not count:
        return {'message': 'Error', 'status': False}
    return {'message': 'Success'}


@record_last_update_timestamp
def add_source_ip(source, token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    try:
        print(source)
        ip_addr = ipaddress.ip_address(source).exploded
    except Exception as e:
        return {'message': str(e), 'status': False}

    if user_dao.add_source_ip(ip_addr, _id):
        doc = user_dao.get_source_ips(_id)
        del doc['_id']
        return doc
    else:
        return {'message': 'Not found user', 'status': False}


@record_last_update_timestamp
def del_source_ip(source, token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    try:
        print(source)
        ip_addr = ipaddress.ip_address(source).exploded
    except Exception as e:
        return {'message': str(e), 'status': False}

    if user_dao.del_source_ip(ip_addr, _id):
        return {'message': 'Delete success', 'status': True}
    else:
        return {'message': f'Not found {ip_addr}', 'status': False}

@record_last_update_timestamp
def get_source_ip(token):
    auth = token.split(' ')
    token_user_info = parse_token(auth[1])
    _id = token_user_info['_id']
    doc = user_dao.get_source_ips(_id)
    del doc['_id']
    if 'source-ips' not in doc:
        return {'source-ips':[]}
    return doc
