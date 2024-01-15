from flask import request, Response
import src.service.fake_as_path_service as fake_as_path_service
from flask import jsonify
from src import app
from utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)


@app.route('/getFakeAsPath', methods=['get'])
def getFakeAsPath():
    st = request.args.get('st')
    et = request.args.get('et')
    return jsonify(fake_as_path_service.getFakeAsPath(st, et))



@app.route('/getFakeAsPathRecordById', methods=['get'])
def getFakeAsPathRecordById():
    _id = request.args.get('id')
    return jsonify(fake_as_path_service.getFakeAsPathRecordById(_id))