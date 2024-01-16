from flask import Flask
from flask_cors import CORS
import json

from src.utils.logger import init_logger
log = init_logger('app')

app = Flask(__name__)
app.logger = log
CORS(app, resources=r'/*')
app.url_map.strict_slashes = False

with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.loads(config_file.read().__str__())
    db_config = config['db']
