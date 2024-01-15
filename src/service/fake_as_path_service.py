import src.model.fake_as_path_dao as fake_as_path_dao
from datetime import datetime
from src.service.app_service import get_as_info_by_list_service
from src.service.util import record_last_update_timestamp
from utils.logger import get_logger, APP_LOG_NAME


@record_last_update_timestamp
def getFakeAsPath(st, et):
    types = ['type1_event', 'type2_aggregated_event']
    result = {}

    for t in types:
        result[t] = []

    for i in fake_as_path_dao.get_data_by_timestamp_from_type1(st, et):
        i['_id'] = i['_id'].__str__()
        result['type1_event'].append(i)

    for i in fake_as_path_dao.get_data_by_timestamp_from_type2(st, et):
        i['_id'] = i['_id'].__str__()
        result['type2_aggregated_event'].append(i)

    return result


@record_last_update_timestamp
def getFakeAsPathRecordById(_id):
    record = fake_as_path_dao.get_type2_record_by_id(_id)
    if record:
        del record['_id']
    return record
