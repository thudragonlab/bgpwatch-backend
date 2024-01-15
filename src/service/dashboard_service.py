import src.model.dashboard_dao as dashboard_dao
from src.service.util import record_last_update_timestamp


@record_last_update_timestamp
def get_prefix_list(asn, query_str):
    prefix_item = dashboard_dao.get_prefix_list(asn)
    if query_str == None:  # Return all prefixes
        response_data = {"ipv4": {}, "ipv6": {}}
        if not prefix_item:
            return response_data
        for pfx in prefix_item['prefixes']:
            if "." in pfx:  # IPv4
                prefix_len = pfx.split("/")[1]
                response_data["ipv4"].setdefault(prefix_len, [])
                response_data["ipv4"][prefix_len].append(pfx)
            else:  # IPv6
                prefix_len = pfx.split("/")[1]
                response_data["ipv6"].setdefault(prefix_len, [])
                response_data["ipv6"][prefix_len].append(pfx)
    else:  # Return prefixes matching query_str
        response_data = []
        if not prefix_item:
            return response_data
        for prefix in prefix_item['prefixes']:
            print(prefix)
            if query_str in prefix:
                response_data.append(prefix)
    return response_data


@record_last_update_timestamp
def get_peer_list(asn, ipversion):
    peer_list = dashboard_dao.get_peer_list(asn)
    if not peer_list:
        return {"import_peers": {}, "export_peers": {}}
    response_data = {"import_peers": peer_list['import'] if 'import' in peer_list else {'ipv4': {}, 'ipv6': {}},
                     "export_peers": peer_list['export'] if 'export' in peer_list else {'ipv4': {}, 'ipv6': {}}}
    # response_data = {"import_peers": peer_list['import'],
    #                  "export_peers": peer_list['export']}
    if ipversion == "4":
        response_data['import_peers'].pop('ipv6')
        response_data['export_peers'].pop('ipv6')
    elif ipversion == "6":
        response_data['import_peers'].pop('ipv4')
        response_data['export_peers'].pop('ipv4')
    return response_data


@record_last_update_timestamp
def get_route_history_stats(qtype, asns, dur):
    asns = asns.split(",")
    response_data = dashboard_dao.get_route_history_stats(asns)

    for data in response_data:
        for key in data:
            if key == "_id":
                continue
            print(list(map(lambda x: f'{"".join(x[0].split("_"))}|{x[1]}', data[key].items())),dur)
            data[key] = list(map(lambda x: f'{"".join(x[0].split("_"))}|{x[1]}', data[key].items()))[-dur:]
            # data[key] = data[key][:dur]
    missing_asn = list(set(asns) - set(list(map(lambda x: x["_id"], response_data))))
    response_data += [{"_id": asn} for asn in missing_asn]
    response_data = sorted(response_data, key=lambda x: asns.index(x["_id"]))
    return response_data

@record_last_update_timestamp
def get_whois_info_by_asn(asn):
    whois_data = dashboard_dao.get_whois_info_by_asn(asn)

    mnt_irt_list = set()
    source_mapping = {}
    for i in whois_data:
        nic_hdl_list = set()

        del i['_id']
        del i['attr_len']
        if 'as-block' in i:
            del i['aut-num']
        inner_list = [i]
        source = i['source']
        if source not in source_mapping:
            source_mapping[source] = []
        # ------role------
        if 'admin-c' in i:
            if type(i['admin-c']).__name__ == 'list':
                for tech in i['admin-c']:
                    nic_hdl_list.add(tech)
            else:
                nic_hdl_list.add(i['admin-c'])

        if 'tech-c' in i:
            if type(i['tech-c']).__name__ == 'list':
                for tech in i['tech-c']:
                    nic_hdl_list.add(tech)
            else:
                nic_hdl_list.add(i['tech-c'])
        if 'abuse-c' in i:
            if type(i['abuse-c']).__name__ == 'list':
                for tech in i['abuse-c']:
                    nic_hdl_list.add(tech)
            else:
                nic_hdl_list.add(i['abuse-c'])


        nic_data = dashboard_dao.get_whois_info_by_nic(list(nic_hdl_list),source)

        for nic_i in nic_data:
            del nic_i['_id']
            del nic_i['attr_len']
            inner_list.append(nic_i)
        # ------irt------
        if 'mnt-irt' in i:
            irt = dashboard_dao.get_one_whois_info_by_irt(i['mnt-irt'],source)
            if irt:
                del irt['_id']
                del irt['attr_len']
                inner_list.append(irt)
            # mnt_irt_list.add(i['mnt-irt'])

        # ------org------
        if 'org' in i:
            org = dashboard_dao.get_one_whois_info_by_org(i['org'])
            if org:
                del org['_id']
                del org['attr_len']
                inner_list.append(org)

        source_mapping[source].append(inner_list)

    # # nic_data = dashboard_dao.get_whois_info_by_nic(list(nic_hdl_list))
    # #
    # # for i in nic_data:
    # #     del i['_id']
    # #     del i['attr_len']
    # #     source = i['source']
    # #     if 'role_info' not in source_mapping[source]:
    # #         source_mapping[source]['role_info'] = []
    # #     source_mapping[source]['role_info'].append(i)
    #
    # irt_data = dashboard_dao.get_whois_info_by_irt(list(mnt_irt_list))
    # for i in irt_data:
    #     # print(i)
    #     del i['_id']
    #     del i['attr_len']
    #     source = i['source']
    #     if 'irt_info' not in source_mapping[source]:
    #         source_mapping[source]['irt_info'] = []
    #     source_mapping[source]['irt_info'].append(i)
    return source_mapping
