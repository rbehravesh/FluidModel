from functools import lru_cache
import network_config as nc
import networkx as nx
from networkx import NetworkXNoPath


@lru_cache(maxsize=None)
def route_path(graph, source, target):
    """
    Find the shortest path from a source node to the target node based one the distance on the links
    """
    try:
        path = nx.shortest_path(graph, source=source, target=target, weight='distance')
    except NetworkXNoPath:
        path = None
    return path


@lru_cache(maxsize=None)
def distance(graph, source, target):
    """
    Find the total distance along the shortest path
    """
    try:
        path = nx.shortest_path(graph, source=source, target=target, weight='distance')
        path_distance = nx.path_weight(graph, path, weight='distance')

    except NetworkXNoPath:
        path_distance = 10**10
    return path_distance


def is_monotonic(graph, s, m, n):
    """
    Checks if a link from 'm' to 'n' starting from the 's' is monotonic or not
    """
    fictitious = 'fic'
    if s == fictitious or m == fictitious or n == fictitious:
        return 1

    n_x = graph.nodes[n]['lon']  # x position
    m_x = graph.nodes[m]['lon']
    s_x = graph.nodes[s]['lon']

    n_y = graph.nodes[n]['lat']  # y position
    m_y = graph.nodes[m]['lat']
    s_y = graph.nodes[s]['lat']

    if abs(n_x - s_x) < abs(m_x - s_x):
        return -1
    if abs(n_y - s_y) < abs(m_y - s_y):
        return -1

    return 1
