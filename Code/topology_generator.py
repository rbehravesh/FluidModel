"""
Generate or load the physical topology
"""

import copy
import time
import networkx as nx
import random
import network_config as nc
from layout import Style as style
from math import cos, asin, sqrt, pi


def get_distance_from_lat_lon_in_meter(latlon1, latlon2):
    """
    Calculate the distance in meters between two latitude-longitude points.
    """
    EARTH_RADIUS_KM = 6371  # Radius of the Earth in kilometers
    lat1, lon1 = latlon1
    lat2, lon2 = latlon2
    p = pi / 180
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return EARTH_RADIUS_KM * asin(sqrt(a)) * 1000  # Distance in meters


def get_absolute_topology_path(base_path, topology_size):
    """
    Construct the absolute file path for a given topology.
    """
    return '{}{}_topology.gml'.format(base_path, topology_size)


def display_error_message(msg, error=None, terminate=False):
    """
    Display an error message and optionally terminate the program.
    """
    print(f"{msg}\n{style.RED}{error}{style.END}")
    if terminate:
        print('The execution is ending...')
        time.sleep(5)
        exit(0)


class Topology:
    """
    Generate or load a network topology based on the given size
    """
    BIG_NUMBER = 9 ** 6

    def __init__(self, topology_id):
        self.graph = None
        self.topology_id = topology_id

        # Initialize sets for datacenters
        self.dc_edge = set()
        self.dc_trans = set()
        self.dc_core = set()
        self.num_dc_edge = 0
        self.num_dc_trans = 0
        self.num_dc_core = 0
        self.dc_share_cap_edge = 0
        self.dc_share_cap_trans = 0
        self.dc_share_cap_core = 0
        self.dc_share_cost_edge = 0
        self.dc_share_cost_trans = 0
        self.dc_share_cost_core = 0

        # Initialize sets for links
        self.e_xn = set()
        self.e_fh = set()
        self.e_trans = set()
        self.e_bh = set()
        self.e_self_links = set()
        self.e = set()
        self.link_share_cap_xn = 0
        self.link_share_cap_fh = 0
        self.link_share_cap_tr = 0
        self.link_share_cap_bh = 0
        self.link_share_cap_inDC = 0
        self.link_share_cost_xn = 0
        self.link_share_cost_fh = 0
        self.link_share_cost_tr = 0
        self.link_share_cost_bh = 0
        self.link_share_cost_inDC = 0

    def get_info(self):
        """
        Print detailed information about the substrate network.
        """
        # Header
        print(f'...............\n'
              f'{style.BOLD}{style.YELLOW}Substrate Network Detailed Information:{style.END}\n'
              '...............')

        # Datacenter information
        print(f'{style.BOLD}{style.DARKCYAN}Datacenters info:{style.END}')
        dc_info = {
            'Edge Datacenters': (self.dc_edge, self.dc_share_cap_edge, self.dc_share_cost_edge),
            'Transport Datacenters': (self.dc_trans, self.dc_share_cap_trans, self.dc_share_cost_trans),
            'Core Datacenters': (self.dc_core, self.dc_share_cap_core, self.dc_share_cost_core)
        }

        for dc_type, (dc_set, dc_cap, dc_cost) in dc_info.items():
            print(f'{dc_type}: {len(dc_set)}, there are {dc_cap} EUC available on each of them, '
                  f'and the cost of each EUC is {dc_cost}')

        # Link information
        print(f'\n{style.BOLD}{style.DARKCYAN}Transport links info:{style.END}')
        link_info = {
            'Links between edge datacenters (Xn)': (self.e_xn, self.link_share_cap_xn, self.link_share_cost_xn),
            'Links between edge and transport datacenters (FH)': (self.e_fh, self.link_share_cap_fh, self.link_share_cost_fh),
            'Links between transport datacenters': (self.e_trans, self.link_share_cap_tr, self.link_share_cost_tr),
            'Links between transport and core datacenters (BH)': (self.e_bh, self.link_share_cap_bh, self.link_share_cost_bh)
        }

        for link_type, (link_set, link_cap, link_cost) in link_info.items():
            print(f'{link_type}: {len(link_set)}, there are {link_cap} EUC available on each of them, '
                  f'and the cost of each EUC is {link_cost}')

    def draw(self):
        """
        Draw the network topology and save it to a file.
        """
        temp_graph = copy.deepcopy(self.graph)
        for n in temp_graph.nodes:
            temp_graph.remove_edge(n, n)

        colors = [n[1] for n in temp_graph.nodes(data="color")]
        try:
            nx.draw(temp_graph, with_labels=True, edge_color="gray", style="solid", node_size=50, font_size=7, width=1,
                    node_color=colors, alpha=1, arrowsize=1, arrowstyle='->',
                    labels={node: node[7:] for node in temp_graph.nodes()})
        except ValueError as e:
            display_error_message('Your topology file (.gml) is corrupted and cannot be drawn.'
                                  ' Please refer to the below ERROR and fix the topology file.', e)

        import pylab as plt
        plt.savefig('TOPOLOGY.png', dpi=1200, bbox_inches='tight')

    def _prepare_topology_details(self):
        """
        Prepare detailed information about the topology based on the graph data.
        """
        # Reset datacenter and link sets
        self.dc_edge = set()
        self.dc_trans = set()
        self.dc_core = set()
        self.e_xn = set()
        self.e_fh = set()
        self.e_trans = set()
        self.e_bh = set()
        self.e_self_links = set()

        # Store physical nodes (datacenters) in their respective variables
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            if 'edge' in node:
                self._add_to_dc_set(node, 'edge', node_data)
            elif 'tran' in node:
                self._add_to_dc_set(node, 'trans', node_data)
            elif 'core' in node:
                self._add_to_dc_set(node, 'core', node_data)

        # Store physical links in their respective variables
        for edge in self.graph.edges():
            self._add_to_link_set(edge)

    def _add_to_dc_set(self, node, dc_type, node_data):
        """
        Add a datacenter node to the appropriate set and update its share capacity and cost.
        """
        getattr(self, f'dc_{dc_type}').add(node)
        setattr(self, f'dc_share_cap_{dc_type}', node_data['shareCap'])
        setattr(self, f'dc_share_cost_{dc_type}', node_data['shareCost'])

    def _add_to_link_set(self, edge):
        """
        Add a link to the appropriate set and update its share capacity and cost.
        """
        m, n = edge
        if m == n:
            self.e_self_links.add((m, n))
        elif m in self.dc_edge and n in self.dc_edge:
            self._update_link_attributes('xn', edge)
        elif (m in self.dc_edge and n in self.dc_trans) or (m in self.dc_trans and n in self.dc_edge):
            self._update_link_attributes('fh', edge)
        elif m in self.dc_trans and n in self.dc_trans:
            self._update_link_attributes('trans', edge)
        elif (m in self.dc_core and n in self.dc_edge) or (m in self.dc_edge and n in self.dc_core):
            self._update_link_attributes('bh', edge)

    def _update_link_attributes(self, link_type, edge):
        """
        Update link attributes for a specific link type.
        """
        m, n = edge
        link_share_cap_attr = f'link_share_cap_{link_type}'
        link_share_cost_attr = f'link_share_cost_{link_type}'

        setattr(self, link_share_cap_attr, self.graph.edges[m, n]['shareCap'])
        setattr(self, link_share_cost_attr, self.graph.edges[m, n]['shareCost'])

    def load_topology_from_file(self, path, size):
        """
        Load a topology from a GML file.
        """
        try:
            self.graph = nx.read_gml(get_absolute_topology_path(path, size))
            self._prepare_topology_details()
        except Exception as e:
            display_error_message('Error loading topology.', e, True)

    def _add_link_to_graph(self, src, dst, level, distance, share_cap, share_cost, latency):
        """
        Add a link to the graph with specified attributes.
        """
        self.graph.add_edge(src, dst, level=level, distance=distance, shareCap=share_cap, shareCost=share_cost,
                            latency=latency, label=level + ' Link')

    def _compute_link_distance(self, src, dst):
        """
        Compute the distance between two nodes.
        """
        return get_distance_from_lat_lon_in_meter(
            (self.graph.nodes[src]['latitude'], self.graph.nodes[src]['longitude']),
            (self.graph.nodes[dst]['latitude'], self.graph.nodes[dst]['longitude'])
        )

    def _add_links_to_graph(self):
        """
        Add all links to the graph based on predefined sets of links.
        """
        for src, dst in self.e:
            distance = self._compute_link_distance(src, dst)
            latency = distance  # We consider latency to be equal to the distance (in milliseconds)
            if src == dst:
                self._add_link_to_graph(src, dst, 'IntraDC', distance, self.link_share_cap_inDC,
                                        self.link_share_cost_inDC, latency)
            elif (src, dst) in self.e_xn:
                self._add_link_to_graph(src, dst, 'Xn', distance, self.link_share_cap_xn,
                                        self.link_share_cost_xn, latency)
            elif (src, dst) in self.e_trans:
                self._add_link_to_graph(src, dst, 'InterTrans', distance, self.link_share_cap_tr,
                                        self.link_share_cost_tr, latency)
            elif (src, dst) in self.e_fh:
                self._add_link_to_graph(src, dst, 'FH', distance, self.link_share_cap_fh,
                                        self.link_share_cost_fh, latency)
            elif (src, dst) in self.e_bh:
                self._add_link_to_graph(src, dst, 'BH', distance, self.link_share_cap_bh,
                                        self.link_share_cost_bh, latency)

    def _add_node_to_graph(self, id_, level, share_cap, share_cost, color, latitude, longitude):
        """
        Add a node to the graph with specified attributes.
        """
        self.graph.add_node(id_, level=level, shareCap=share_cap, shareCost=share_cost, color=color, latitude=latitude,
                            longitude=longitude)

    def _add_nodes_to_graph(self):
        """
        Add all nodes to the graph based on predefined sets of nodes.
        """
        for n in sorted(self.dc_edge):
            self._add_node_to_graph(n, 'Edge', self.dc_share_cap_edge, self.dc_share_cost_edge, '#7870b4',
                                    latitude=random.uniform(40.253602, 40.27668),
                                    longitude=random.uniform(-3.77504, -3.737746))

        # # Add transport DCs to the graph (Uncomment this in case you have transport nodes in the topology like 5GEN)
        # for n in self.dc_trans:
        #     self._add_node_to_graph(n, 'Trans', self.dc_share_cap_trans, self.dc_share_cost_trans, '#780000',
        #                             latitude=random.uniform(40.2585977130845, 40.274018792148),
        #                             longitude=random.uniform(-3.766972, -3.7423032373))

        # Add core DCs to the graph
        for n in self.dc_core:
            self._add_node_to_graph(n, 'Core', self.dc_share_cap_core, self.dc_share_cost_core, '#787000',
                                    latitude=random.uniform(40.2647663628264, 40.2674002969022),
                                    longitude=random.uniform(-3.75721197590123, -3.75380601283906))

    def load_topology(self, path_to_the_topology):
        try:
            # Attempt to load the topology from the file
            self.load_topology_from_file(path_to_the_topology, self.topology_id)
            self.draw()
        except Exception as e:
            # Handle any exceptions that occur during loading and drawing
            error_message = f"Error loading topology: {str(e)}"
            print(error_message)

        return self.graph, self.dc_edge
