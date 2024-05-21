from functools import lru_cache
import networkx as nx
from networkx import NetworkXNoPath


class GraphUtilities:
    def __init__(self, graph):
        self.graph = graph

    def validate_graph_node(self, node):
        """
        Validate if a node exists in the graph.
        """
        if node not in self.graph:
            raise ValueError(f"Node '{node}' not found in the graph.")

    @lru_cache(maxsize=None)
    def get_shortest_path(self, source, target):
        """
        Get the shortest path between source and target in a graph.
        """
        try:
            self.validate_graph_node(source)
            self.validate_graph_node(target)
            return nx.shortest_path(self.graph, source=source, target=target, weight='distance'), True
        except NetworkXNoPath:
            return None, False
        except ValueError as e:
            print(f"Validation Error: {e}")
            return None, False

    # @lru_cache(maxsize=None)
    def route_path(self, source, target):
        """
        Find the shortest path from a source node to the target node based on the distance on the links.
        """
        path, _ = self.get_shortest_path(source, target)
        return path

    @lru_cache(maxsize=None)
    def distance(self, source, target):
        """
        Find the total distance along the shortest path.
        """
        path, path_exists = self.get_shortest_path(source, target)
        if path_exists:
            return nx.path_weight(self.graph, path, weight='distance')
        else:
            return 10**10  # Return a big number to avoid choosing that path

    def is_monotonic(self, s, m, n):
        """
        Checks if a link from 'm' to 'n' starting from the 's' is monotonic or not.
        """
        fictitious = 'fic'
        if any(node == fictitious for node in [s, m, n]):
            return 1

        try:
            for node in [s, m, n]:
                self.validate_graph_node(node)

            n_coord = (self.graph.nodes[n]['longitude'], self.graph.nodes[n]['latitude'])
            m_coord = (self.graph.nodes[m]['longitude'], self.graph.nodes[m]['latitude'])
            s_coord = (self.graph.nodes[s]['longitude'], self.graph.nodes[s]['latitude'])

            return -1 if any(abs(n_coord[i] - s_coord[i]) < abs(m_coord[i] - s_coord[i]) for i in range(2)) else 1
        except ValueError as e:
            print(f"Validation Error in is_monotonic: {e}")
            return None
        except KeyError as e:
            print(f"Key Error in graph node data: {e}")
            return None
