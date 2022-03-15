"""
Compute distance between physical DCs
"""

import networkx as nx


class Distance:

    @classmethod
    def get_distance_from_lat_lon_in_meter(cls, m, n):
        from math import cos, asin, sqrt, pi
        lat1 = m[0]
        lon1 = m[1]
        lat2 = n[0]
        lon2 = n[1]

        p = pi / 180
        a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
        return (12742 * asin(sqrt(a))) * 1000  # 2*R*asin

    @classmethod
    def path_dist_calc(cls, graph, path):
        """
        Calculate the distance value of monotonic paths
        * it gets the monotonic paths as input and calculate the total distance from the source node to the destination
        """
        path_dist = 0
        for n in range(len(path) - 1):
            if (path[n], path[n + 1]) in graph.edges:
                path_dist += cls.get_distance_from_lat_lon_in_meter((graph.nodes[path[n]]['lat'], graph.nodes[path[n]]['lon']),
                            (graph.nodes[path[n + 1]]['lat'], graph.nodes[path[n + 1]]['lon']))
        return path_dist

    @classmethod
    def distance(cls, graph, s, d):
        """
        Find the monotonic paths from each given source to the given destination
         - use Dijkstra to find the paths
         - call a func to calculate the path distance value
        """
        path = nx.dijkstra_path(graph, source=s, target=d, weight='distance')
        val = cls.path_dist_calc(graph, path)
        return val

    @classmethod
    def ismonotonic(cls, graph, s, m, n):
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