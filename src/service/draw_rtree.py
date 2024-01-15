import os
from typing import List, Tuple, NewType, Dict, Union
from graphviz import Digraph
import numpy as np
import json

# from src import resilience_path

LinkType = NewType('LinkType', Tuple[Union[str, int], Union[str, int]])
graph_format = 'png'
condition: Union[str, None] = None
cone_data: Union[Dict[str, int], None] = None


def make_links_and_name(dataset_inner):
    name_map = {}
    name: List[str] = []
    links_inner: List[LinkType] = []

    row = [str(i_in) for i_in in dataset_inner['row']]
    col = [str(i_in) for i_in in dataset_inner['col']]
    link = list(zip(row, col))
    for ll in link:
        if is_meeting_condition(ll):
            a, b_in = ll
            name_map[a] = 1
            name_map[b_in] = 1

            if a == '38235':
                print(ll)
            # if b_in == '38235':
            #     print(ll)
            links_inner.append(LinkType((str(b_in), str(a))))

    for i_in in name_map:
        name.append(str(i_in))
    return name, links_inner


def draw_graph(name: str, nodes_inner: List[str], edges: List[LinkType], output_path: str) -> str:
    dot = Digraph(name='myPicture', format=graph_format)
    asn = name[9:]
    for n in nodes_inner:
        if n == asn:
            dot.node(name=n, style='filled', color='black', fontcolor='white')
        else:
            dot.node(name=n)
    for link in edges:
        dot.edge(link[0], link[1])

    if condition is not None and cone_data is not None:
        dot.render(filename=f'{name}-{condition}', cleanup=True, directory=output_path)
        graph_path = os.path.join(output_path, f'{name}-{condition}.{graph_format}')
    else:
        dot.render(filename=name, cleanup=True, directory=output_path)
        graph_path = os.path.join(output_path, f'{name}.{graph_format}')
    return graph_path


def draw_rtree_diff_graph(npz_path: str, output_path: str) -> str:
    dataset = np.load(npz_path, allow_pickle=True)
    nodes, links = make_links_and_name(dataset)
    file_name = npz_path.split('/')[-1][:-4]
    return draw_graph(file_name, nodes, links, output_path)


def is_meeting_condition(line):
    global condition
    global cone_data
    left_result = True
    right_result = True
    if condition is not None and cone_data is not None:
        a, b = line
        a = str(a)
        b = str(b)
        left_c, right_c = condition.split(',')
        left_n = left_c[1:]
        right_n = right_c[:-1]
        left_symbol = left_c[0]
        right_symbol = right_c[-1]

        if left_n:
            if left_symbol == '[':
                left_result = cone_data[a] >= int(left_n)
            elif left_symbol == '(':
                left_result = cone_data[a] > int(left_n)

        if right_n:
            if right_symbol == ']':
                right_result = cone_data[b] <= int(right_n)
            elif right_symbol == ')':
                right_result = cone_data[b] < int(right_n)

    # 没进判断则当作没有条件
    return left_result and right_result


def draw_rtree(asn: str, cc: str, output_path: str, _graph_format: str, _condition: str) -> str:
    global graph_format
    global condition
    global cone_data
    graph_format = _graph_format
    if _condition:
        condition = _condition
        with open(f'resilience_data/topo_graph_for_frontend/{cc}_cone.json', 'r') as ff:
            cone_data = json.load(ff)
    # print(condition)
    file_name = f'dcomplete{asn}.npz'
    # dst_path = f'static/{file_name}'
    dst_path = f'resilience_data/rtree_graph_data/{cc}/dcomplete{asn}.npz'

    # source_path = os.path.join(resilience_path, 'output/asRank/rtree', cc, file_name)
    # cmd = f'scp 203.91.121.231:{source_path} {dst_path}'
    # with os.popen(cmd, 'r') as f:
    #     print(f'scp cmd -> {cmd}', f)
    #
    # if not os.path.exists(dst_path):
    #     raise Exception('Download Failure: Not Found file')
    graph_path = draw_rtree_diff_graph(dst_path, output_path)
    os.remove(dst_path)
    condition = None
    cone_data = None
    return graph_path


def draw_graph_by_prefix(name: str, nodes_inner: List[str], edges: List[LinkType], output_path: str) -> str:
    dot = Digraph(name='myPicture', format=graph_format)
    for (index, n) in enumerate(nodes_inner):
        if n == 'org_prefix':
            dot.node(name=str(n), label=str(name.replace('-', '/')))
        else:
            dot.node(name=str(n), label=str(n))
    for link in edges:
        dot.edge(str(link[0]), str(link[1]))

    dot.render(filename=name, cleanup=True, directory=output_path)
    graph_path = os.path.join(output_path, f'{name}.{graph_format}')
    return graph_path
