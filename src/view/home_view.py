import src.service.home_service as home_service
from flask import jsonify, request

from src import app
from src.utils.logger import get_logger, APP_LOG_NAME

log = get_logger(APP_LOG_NAME)


@app.route('/stats', methods=['get'])
def stats():
    start = request.args.get('start')
    end = request.args.get('end')
    return jsonify(home_service.stats(start, end))


@app.route('/overview', methods=['get'])
def overview():
    start = request.args.get('start')
    end = request.args.get('end')
    cc = request.args.get('cc')
    asn = request.args.get('asn')
    if cc and len(cc) == 2:
        cc = cc.upper()
    else:
        cc = None

    if asn:
        try:
            int(asn)
        except ValueError:
            return jsonify({
                'status': 'failed',
                'statusCode': 'Invalid ASN!'
            })
    start = int(start) / 1000
    end = int(end) / 1000
    return jsonify(home_service.overview(start, end, cc, asn))

# @app.route('/exportCSV', methods=['get'])
# def exportCSV():
#     # DISABLE
#     start = request.args.get('start')
#     end = request.args.get('end')
#     start = int(start) / 1000
#     end = int(end) / 1000
#
#     return home_service.exportCSV(start, end)
