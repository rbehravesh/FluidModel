from select import poll

from networkx import NetworkXNoPath

import timeit
import networkx as nx
from layout import Style as style
from heuristic import print_output
from functools import lru_cache

previous_checks_dict = {}


def service_embedding(users, graph, fictitious_dc):
    """
    Embed services onto the network
    """
    from heuristic import print_output
    print(f'{style.YELLOW}=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-={style.END}')
    print(f'{style.BOLD}{style.DARKCYAN}Results of the SOTA{style.END}')
    print(f'{style.YELLOW}=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-={style.END}')

    total_cost = 0
    run_time_start = timeit.default_timer()
    users_on_fictitious = set()
    share_amount_on_fictitious = 0

    edge_share_utilization = 0
    trans_share_utilization = 0
    core_share_utilization = 0

    rejected_users = set()
    share_amount_rejected = 0
    for u in users:
        # Dictionaries to store allocation decisions
        direct_allocation = {}
        transient_allocation = {}

        s = u.assoc_dc
        for i, j in u.app_demand.edges():
            target_node, path = get_a_node_and_its_path(u, s, graph, i, j)

            # if there is no node or link to embed user request then that user is rejected
            # All the allocated resources should be taken back
            if target_node is None or path is None:
                rejected_users.add(u)
                share_amount_rejected += u.share_demand
                # deallocate_resources(u, direct_allocation, transient_allocation)
                break

            # Transient Links allocation
            if len(path) > 1:
                for index in range(len(path) - 2):
                    m, n = (path[index], path[index + 1])
                    transient_allocation[u, u.app_demand, s, i, j, m, n] = u.share_demand

                    graph.edges[m, n]['shareCap'] -= u.share_demand * u.app_demand.edges[i, j]['shareMultiplier']
                    if s != fictitious_dc and m != fictitious_dc and n != fictitious_dc:
                        total_cost += graph.edges[m, n]['shareCost'] * \
                                           u.share_demand * u.app_demand.edges[i, j]['shareMultiplier']

                # Direct Links allocation
                m, n = (path[-2], path[-1])

            # if it should be placed on the source node
            if len(path) == 1:
                m, n = (path[0], path[0])

            direct_allocation[u, u.app_demand, s, i, j, m, n] = u.share_demand
            graph.edges[m, n]['shareCap'] -= u.share_demand * u.app_demand.edges[i, j]['shareMultiplier']

            graph.nodes[target_node]['shareCap'] -= u.share_demand * u.app_demand.nodes[j]['shareMultiplier']

            s = target_node

            if 'edge' in n:
                edge_share_utilization += u.share_demand * u.app_demand.nodes[j]['shareMultiplier']
            elif 'tran' in n:
                trans_share_utilization += u.share_demand * u.app_demand.nodes[j]['shareMultiplier']
            elif 'core' in n:
                core_share_utilization += u.share_demand * u.app_demand.nodes[j]['shareMultiplier']

            if s != fictitious_dc and m != fictitious_dc and n != fictitious_dc:
                total_cost += (graph.edges[(m, n)]['shareCost'] * u.share_demand * u.app_demand.edges[i, j]['shareMultiplier']) \
                              + graph.nodes[n]['shareCost'] * u.share_demand * u.app_demand.nodes[j]['shareMultiplier']

        # print_output('Direct', direct_allocation)
        # print_output('Transient', transient_allocation)


        if fictitious_dc is not None:
            for u_, a, s, i, j, m, n in direct_allocation:
                if direct_allocation[u_, a, s, i, j, m, n] and n.startswith('fic'):
                    users_on_fictitious.add(u_)

    share_amount_on_fictitious += sum((u.share_demand for u in users_on_fictitious))

    run_time_stop = timeit.default_timer()
    exec_time = run_time_stop - run_time_start

    import heuristic
    heuristic.print_rejected_users(rejected_users, share_amount_rejected, len(users_on_fictitious),
                                   share_amount_on_fictitious, 'SOTA summary')

    return [len(rejected_users), share_amount_rejected,
            len(users_on_fictitious), share_amount_on_fictitious,  exec_time, total_cost,
            edge_share_utilization, trans_share_utilization, core_share_utilization]


def deallocate_resources(u, direct_allocation, transient_allocation):
    """If a function cannot be embedded for a user the whole resource allocated to that user should be deallocated"""
    pass


def get_a_node_and_its_path(u, s, graph, i, j):
    """
    Select a node to place function j and then return the node and the path from the function i to that node
    """
    selected_node = None
    selected_path = None
    for target_node in sorted(graph.nodes(), key=lambda target_node:graph.nodes[target_node]['shareCost'],
                              reverse=False):
        # the terminator function should be placed on the same node as the last function, which is s
        if j == 'T':
            return s, [s]

        if not is_node_capacity_constraint_satisfied(u, j, graph, target_node):
            continue

        path = find_path_from_previous_checks(graph, s, target_node, u, i, j)
        if path is None:
            path = find_shortest_path(graph, source=s, target=target_node, weight='distance')

        if path is None:
            continue

        if not is_link_capacity_constraint_satisfied(u, i, j, graph, path):
            continue

        path_distance = get_distance(graph, tuple(path))

        if not is_latency_constraint_satisfied(u, i, j, latency_on_the_path=path_distance):
            continue

        # if is_exceeding_hops(path):
        #     continue

        selected_node = target_node
        selected_path = path

        return [selected_node, selected_path]

    return [selected_node, selected_path]


def is_exceeding_hops(path):
    if len(path) > 3:
        return True
    return False


def is_latency_constraint_satisfied(u, i, j, latency_on_the_path):
    # check if the founded path from s to the target node can satisfy latency requirement of the logical link (i, j)
    if u.app_demand.edges[i, j]['latencyDemand'] >= latency_on_the_path:
        return True
    return False


def is_node_capacity_constraint_satisfied(u, j, graph, target_node):
    # check if the target node has the required computing capacity (ECU)

    return graph.nodes[target_node]['shareCap'] >= \
           u.app_demand.nodes[j]['shareMultiplier'] * u.share_demand


def is_link_capacity_constraint_satisfied(u, i, j, graph, path):
    # check if all the physical links on the founded path have enough capacity (ECU) on the links
    for index in range(len(path) - 1):
        e = (path[index], path[index + 1])
        if graph.edges[e]['shareCap'] <= 1:
            graph.edges[e]['distance'] = 10*20
        if graph.edges[e]['shareCap'] <= u.share_demand * u.app_demand.edges[i, j]['shareMultiplier']:
            return False
    return True


@lru_cache(maxsize=None)
def get_distance(graph, path):
    """
    Find the total distance along the shortest path
    """
    try:
        path_distance = nx.path_weight(graph, path, weight='distance')
    except NetworkXNoPath:
        path_distance = 9**10

    return path_distance


# @lru_cache(maxsize=None)
def find_shortest_path(graph, source, target, weight=None):
    try:
        path = nx.shortest_path(graph, source=source, target=target, weight='distance')
        # path = nx.shortest_path(graph, source=source, target=target)
    except NetworkXNoPath:
        path = None
    return path


def find_a_new_path(graph, s, target, u, i, j):
    try:
        paths = find_shortest_paths(graph, source=s, target=target, weight='distance')
        while True:
            try:
                path = next(paths)
                if is_link_capacity_constraint_satisfied(u, i, j, graph, path):
                    previous_checks_dict[(s, target)] = path
                    break
            except StopIteration:
                path = None
                break
    except NetworkXNoPath:
        path = None

    return path


@lru_cache(maxsize=None)
def check_dic_of_paths(source, target):
    return previous_checks_dict[(source, target)]


def find_path_from_previous_checks(graph, s, target_node, u, i, j):
    try:
        path = check_dic_of_paths(s, target_node)
        if not is_link_capacity_constraint_satisfied(u, i, j, graph, path):
            path = None
    except KeyError:
        path = None

    return path
