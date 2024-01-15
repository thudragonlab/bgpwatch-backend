import logging
from logging.handlers import RotatingFileHandler


APP_LOG_NAME = 'app'
INTERVAL_LOG_NAME = 'schedule'
ROUTING_PATH_LOG_NAME = 'routing_path'
WHOIS_LOG_NAME = 'whois'
JITTER_LOG_NAME = 'jitter'
ROA_LOG_NAME = 'roa'
MONITOR_LOG_NAME = 'monitor'


def set_logger_config(logger, log_name):
    logging.basicConfig(level=logging.DEBUG)
    handler = RotatingFileHandler(f'./logs/{log_name}.log', encoding='UTF-8', maxBytes=5 * 1024 * 1024, backupCount=10)
    handler.setLevel(logging.DEBUG)
    logging_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
    logger.addHandler(handler)


def init_logger(logger_name):
    logger = logging.getLogger(logger_name)
    set_logger_config(logger, logger_name)
    return logger


def get_logger(logger_name):
    return logging.getLogger(logger_name)
