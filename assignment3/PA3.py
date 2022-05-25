import sys, queue
from typing import List, Dict, Tuple


class PQNode:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __lt__(self, other):
        return self.b < other.b


interfaces: List[str] = []
interface_map: Dict[str, int] = {}
interface_map_tmp: Dict[str, bool] = {}
nodes: List[List[int]] = []
graph: List[List[Tuple[int, int]]] = []  # to, weight
nodes_interfaces: List[Dict[int, int]] = []  # nodes_interfaces[i] = {to: interface_id}
raw_subnets: Dict[str, List[int]] = {}


def get_node(v):
    for i in range(len(nodes)):
        if v in nodes[i]:
            return i


def get_subnet_ip(ip):
    addresses, mask = ip.split('/')
    quarters = addresses.split('.')
    bin_mask = (~0) << (32 - int(mask))
    bin_ip = 0
    for i in range(4):
        bin_ip = bin_ip | (int(quarters[3 - i]) << (8 * i))
    bin_ip = bin_ip & bin_mask
    for i in range(4):
        quarters[3 - i] = str((bin_ip >> (8 * i)) & 0xff)
    return '.'.join(quarters) + '/' + mask


def solve_path(start, end):
    dis = [2147483647 for i in range(len(graph))]
    shortest_from = [0 for i in range(len(graph))]
    pq = queue.PriorityQueue()
    pq.put(PQNode(start, 0))
    dis[start] = 0
    while pq.qsize() != 0:
        node = pq.get()
        dist = node.a
        now = node.b
        if dis[dist] < now:
            continue
        for v in graph[dist]:
            nxt = v[0]
            d = dis[dist] + v[1]
            if d < dis[nxt]:
                dis[nxt] = d
                pq.put(PQNode(nxt, d))
                shortest_from[nxt] = dist
    # print(shortest_from)
    now = end
    res = []
    while now != start:
        nxt = shortest_from[now]
        res.append(interfaces[nodes_interfaces[now][nxt]])
        res.append(interfaces[nodes_interfaces[nxt][now]])
        now = nxt
    return res


def solve_table(ifs, router):
    res = {"dc": [], "via": []}
    for subnet in raw_subnets:
        if subnet in ifs:
            res["dc"].append(subnet)
        else:
            res["via"].append((subnet, solve_path(router, raw_subnets[subnet][0])[-1]))
    return res


def ip_to_int(ip):
    res = 0
    sp = ip.split('.')
    res |= int(sp[0]) << 24
    res |= int(sp[1]) << 16
    res |= int(sp[2]) << 8
    res |= int(sp[3])
    return res


def int_to_ip(i):
    return "%d.%d.%d.%d" % ((i >> 24) & 255, (i >> 16) & 255, (i >> 8) & 255, i & 255)


def aggregate(a: str, b: str):
    addr_a, mask_a = a.split('/')
    addr_b, mask_b = b.split('/')
    mask_a = int(mask_a)
    mask_b = int(mask_b)
    if mask_a < 16 or mask_b < 16:
        return None
    addr_int_xor = ip_to_int(addr_a) ^ ip_to_int(addr_b)
    l = 32
    for i in range(32):
        if ((addr_int_xor >> (31 - i)) & 1) != 0:
            l = i
            break
    if l >= 16:
        return int_to_ip((ip_to_int(addr_a) >> (32 - l)) << (32 - l)) + "/" + str(l)
    return None


def aggregate_table(via: List[Tuple[str, str]]):
    via_map = {}
    ans = []
    for route in via:
        if route[1] not in via_map:
            via_map[route[1]] = []
        if route[0] not in via_map[route[1]]:
            via_map[route[1]].append(route[0])
    for k in via_map:
        res = []
        while len(via_map[k]) != 0:
            for i in range(1, len(via_map[k])):
                t = aggregate(via_map[k][0], via_map[k][i])
                if t is not None:
                    via_map[k][0] = t
                    via_map[k].pop(i)
                    break
            res.append(via_map[k].pop(0))
        via_map[k] = res
    for k in via_map:
        for v in via_map[k]:
            ans.append((v, k))
    return ans


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        for interface in f.readline()[:-1].split(' '):
            interface_map[interface] = len(interfaces)
            interface_map_tmp[interface] = False
            interfaces.append(interface)
            subnet_ip = get_subnet_ip(interface)
            if subnet_ip not in raw_subnets:
                raw_subnets[subnet_ip] = []

        for router in f.readline()[:-1].split(' '):
            tmp = []
            for port in router[1:-1].split(','):
                interface = port.strip("'")
                tmp.append(interface_map[interface])
                interface_map_tmp[interface] = True
                raw_subnets[get_subnet_ip(interface)].append(len(nodes))
            nodes.append(tmp)
        for key in interface_map_tmp:
            if not interface_map_tmp[key]:
                nodes.append([interface_map[key]])

        for i in range(len(nodes)):
            graph.append([])
            nodes_interfaces.append({})
        for edge in f.readline()[:-1].split(' '):
            tmp = edge[1:-1].split(',')
            u = interface_map[tmp[0].strip('\'')]
            v = interface_map[tmp[1].strip('\'')]
            node_u = get_node(u)
            node_v = get_node(v)
            w = int(tmp[2])
            graph[node_u].append((node_v, w))
            graph[node_v].append((node_u, w))
            nodes_interfaces[node_u][node_v] = u
            nodes_interfaces[node_v][node_u] = v

        for i in range(int(f.readline()[:-1])):
            case = f.readline()[:-1].split(' ')
            if case[0] == 'PATH':
                start = get_node(interface_map[case[1].strip()])
                end = get_node(interface_map[case[2].strip()])
                ans = ""
                for interface in solve_path(start, end):
                    ans = interface.split('/')[0] + " " + ans
                print(ans)
            elif case[0] == 'TABLE':
                ifs = [i.strip('\'') for i in case[1][1:-1].split(',')]
                for i in range(len(nodes)):
                    if interface_map[ifs[0]] in nodes[i]:
                        table = solve_table([get_subnet_ip(i) for i in ifs], i)
                        before_agg = []
                        after_agg = []
                        for v in table["dc"]:
                            before_agg.append(v + " is directly connected")
                            after_agg.append(v + " is directly connected")
                        for v in table["via"]:
                            before_agg.append(v[0] + " via " + v[1].split('/')[0])
                        before_agg.sort()
                        for v in before_agg:
                            print(v)
                        print("After")
                        for v in aggregate_table(table["via"]):
                            after_agg.append(v[0] + " via " + v[1].split('/')[0])
                        after_agg.sort()
                        for v in after_agg:
                            print(v)
