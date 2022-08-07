"""
Generate or load the physical topology
"""

import copy
import time
import networkx as nx
import random
import network_config as nc
from layout import Style as style


def get_distance_from_lat_lon_in_meter(m, n):
    from math import cos, asin, sqrt, pi
    lat1 = m[0]
    lon1 = m[1]
    lat2 = n[0]
    lon2 = n[1]

    p = pi / 180
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return (12742 * asin(sqrt(a))) * 1000  # 2*R*asin


def _get_abs_location(path_to_the_topology, topology_size):
    return '{}{}_topology.gml'.format(path_to_the_topology, topology_size)


def error_message(msg, e=None, finish=False, ):
    print(msg)
    print(style.RED, e, style.END)
    if finish:
        print('The execution is ending...')
        time.sleep(5)
        exit(0)


class Topology:
    """
    Generate or load a network topology based on the given size
    """
    BIG_NUMBER = 999999999

    def __init__(self):
        self.graph = None

        # Dcs
        self.dc_edge = set()
        self.dc_trans = set()
        self.dc_core = set()

        self.num_dc_edge = 0
        self.num_dc_trans = 0
        self.num_dc_core = 0

        # Links
        self.e_xn = set()
        self.e_fh = set()
        self.e_trans = set()
        self.e_bh = set()
        self.e_self_links = set()
        self.e = set()

        # Capacity
        self.dc_share_cap_edge = 0
        self.dc_share_cap_trans = 0
        self.dc_share_cap_core = 0

        self.link_share_cap_inDC = 0
        self.link_share_cap_xn = 0
        self.link_share_cap_tr = 0
        self.link_share_cap_fh = 0
        self.link_share_cap_bh = 0

        # Cost
        self.dc_share_cost_edge = 0
        self.dc_share_cost_trans = 0
        self.dc_share_cost_core = 0

        self.link_share_cost_inDC = 0
        self.link_share_cost_xn = 0
        self.link_share_cost_tr = 0
        self.link_share_cost_fh = 0
        self.link_share_cost_bh = 0

    def get_info(self):

        print(f'...............\n'
              f'{style.BOLD}{style.YELLOW}Substrate Network Detailed Information:{style.END}\n'
              '...............')
        print(f'{style.BOLD}{style.DARKCYAN}Datacenters info:{style.END}')
        print(f'Edge Datacenters: {len(self.dc_edge)}, there are {self.dc_share_cap_edge}'
              f'EUC available on each of them, and the cost of each EUC is {self.dc_share_cost_edge}')

        print(f'Transport Datacenters: {len(self.dc_trans)}, there are {self.dc_share_cap_trans}'
              f' EUC available on each of them, and the cost of each EUC is {self.dc_share_cost_trans}')

        print(f'Core Datacenters: {len(self.dc_core)}, there are {self.dc_share_cap_core}'
              f' EUC available on each of them, and the cost of each EUC is {self.dc_share_cost_core}\n')

        print(f'{style.BOLD}{style.DARKCYAN}Transport links info:{style.END}')
        print(f'Links between edge datacenters (Xn): {len(self.e_xn)}, there are {self.link_share_cap_xn} '
              f'EUC available on each of them, and the cost of each EUC is {self.link_share_cost_xn}')

        print(f'Links between edge and transport datacenters (FH): {len(self.e_fh)}, there are {self.link_share_cap_fh} '
              f'EUC available on each of them, and the cost of each EUC is {self.link_share_cost_fh}')

        print(f'Links between transport datacenters: {len(self.e_trans)}, there are {self.link_share_cap_tr} '
              f'EUC available on each of them, and the cost of each EUC is {self.link_share_cost_tr}')

        print(f'Links between transport and core datacenters (BH): {len(self.e_bh)}, there are {self.link_share_cap_bh} '
              f'EUC available on each of them, and the cost of each EUC is {self.link_share_cost_bh}')

    def draw(self):
        temp_graph = copy.deepcopy(self.graph)
        for n in temp_graph.nodes:
            temp_graph.remove_edge(n, n)

        colors = [n[1] for n in temp_graph.nodes(data="color")]
        try:
            nx.draw(temp_graph, with_labels=True, edge_color="gray", style="solid", node_size=50, font_size=7, width=1,
                    node_color=colors, alpha=1, arrowsize=1, arrowstyle='->',
                    labels={node: node[7:] for node in temp_graph.nodes()})
        except ValueError as e:
            error_message('Your topology file (.gml) is corrupted and cannot be drawn.'
                          ' Please refer to the below ERROR and fix the topology file.', e)

        import pylab as plt
        plt.savefig('TOPOLOGY.png', dpi=1200, bbox_inches='tight')

    def _get_detailed_topology(self):
        """
        Prepare the topology and store the details of the topology into different sets/variables and return them
        """
        # store physical nodes (datacenters) in their respective variables
        for n in self.graph.nodes():
            if 'edge' in n:
                self.dc_edge.add(n)
                self.dc_share_cap_edge = self.graph.nodes[n]['shareCap']
                self.dc_share_cost_edge = self.graph.nodes[n]['shareCost']
            elif 'tran' in n:
                self.dc_trans.add(n)
                self.dc_share_cap_trans = self.graph.nodes[n]['shareCap']
                self.dc_share_cost_trans = self.graph.nodes[n]['shareCost']
            elif 'core' in n:
                self.dc_core.add(n)
                self.dc_share_cap_core = self.graph.nodes[n]['shareCap']
                self.dc_share_cost_core = self.graph.nodes[n]['shareCost']

        # store physical links in their respective variables
        for m, n in self.graph.edges():
            if m == n:
                self.e_self_links.add((m, n))
            elif m in self.dc_edge and n in self.dc_edge and m != n:
                self.e_xn.add((m, n))
                self.link_share_cap_xn = self.graph.edges[m, n]['shareCap']
                self.link_share_cost_xn = self.graph.edges[m, n]['shareCost']
            elif (m in self.dc_edge and n in self.dc_trans) or (m in self.dc_trans and n in self.dc_edge):
                self.e_fh.add((m, n))
                self.link_share_cap_fh = self.graph.edges[m, n]['shareCap']
                self.link_share_cost_fh = self.graph.edges[m, n]['shareCost']
            elif m in self.dc_trans and n in self.dc_trans and m != n:
                self.e_trans.add((m, n))
                self.link_share_cap_tr = self.graph.edges[m, n]['shareCap']
                self.link_share_cost_tr = self.graph.edges[m, n]['shareCost']
            elif (m in self.dc_core and n in self.dc_trans) or (m in self.dc_trans and n in self.dc_core):
                self.e_bh.add((m, n))
                self.link_share_cap_bh = self.graph.edges[m, n]['shareCap']
                self.link_share_cost_bh = self.graph.edges[m, n]['shareCost']

    def load_topology_from_file(self, path_to_the_topology, topology_size):
        try:
            self.graph = nx.read_gml(_get_abs_location(path_to_the_topology, topology_size))
            self._get_detailed_topology()
        except FileNotFoundError as e:
            error_message('The given path or the file name for loading the topology does not exist.', e, True)
        except KeyError as e:
            error_message('There is a key error in the topology file. \nKey: ', e, True)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    """
    Generate a new topology based on the parameters given in network_config.py file
    """
    def _add_link_to_graph(self, src, dst, level, distance, share_cap, share_cost, latency):

        self.graph.add_edge(src, dst, level=level, distance=distance, shareCap=share_cap, shareCost=share_cost,
                            latency=latency, label=level + ' Link')

    def _compute_link_dist(self, src, dst):
        return get_distance_from_lat_lon_in_meter(
                (self.graph.nodes[src]['latitude'], self.graph.nodes[src]['longitude']),
                (self.graph.nodes[dst]['latitude'], self.graph.nodes[dst]['longitude'])
        )

    def _add_links_to_graph(self):
        for src, dst in self.e:
            distance = self._compute_link_dist(src, dst)
            latency = distance  # We consider latency to be equal to the distance (in milliseconds)
            if src == dst:
                self._add_link_to_graph(src, dst, 'IntraDC', distance, self.link_share_cap_inDC,
                                        self.link_share_cost_inDC, latency)
            if (src, dst) in self.e_xn:
                self._add_link_to_graph(src, dst, 'Xn', distance, self.link_share_cap_xn,
                                        self.link_share_cost_xn, latency)
            if (src, dst) in self.e_trans:
                self._add_link_to_graph(src, dst, 'InterTrans', distance, self.link_share_cap_tr,
                                        self.link_share_cost_tr, latency)
            if (src, dst) in self.e_fh:
                self._add_link_to_graph(src, dst, 'FH', distance, self.link_share_cap_fh,
                                        self.link_share_cost_fh, latency)
            if (src, dst) in self.e_bh:
                self._add_link_to_graph(src, dst, 'BH', distance, self.link_share_cap_bh,
                                        self.link_share_cost_bh, latency)

    def _create_links(self, first_set, second_set, isbh=False):
        links = set()
        for n in first_set:
            dist = Topology.BIG_NUMBER
            candidate = None
            for m in second_set:
                if m != n:
                    if get_distance_from_lat_lon_in_meter((self.graph.nodes[m]['latitude'],
                                                           self.graph.nodes[m]['longitude']),
                                                          (self.graph.nodes[n]['latitude'],
                                                           self.graph.nodes[n]['longitude'])) < dist:

                        dist = get_distance_from_lat_lon_in_meter((self.graph.nodes[m]['latitude'],
                                                                   self.graph.nodes[m]['longitude']),
                                                                  (self.graph.nodes[n]['latitude'],
                                                                   self.graph.nodes[n]['longitude']))
                        candidate = m

            if n is not None and candidate is not None:
                links.add((n, candidate))
                links.add((candidate, n))

        # this is added to have connection from each transport node to all the cores
        if isbh:
            for n in self.dc_core:
                for m in self.dc_trans:
                    links.add((n, m))
                    links.add((m, n))

        return links

    def _add_node_to_graph(self, id_, level, share_cap, share_cost, color, latitude, longitude):

        self.graph.add_node(id_, level=level, shareCap=share_cap, shareCost=share_cost, color=color, latitude=latitude,
                            longitude=longitude)

    def _add_nodes_to_graph(self):
        for n in sorted(self.dc_edge):
            self._add_node_to_graph(n, 'Edge', self.dc_share_cap_edge, self.dc_share_cost_edge, '#7870b4',
                                    latitude=random.uniform(40.253602, 40.27668),
                                    longitude=random.uniform(-3.77504, -3.737746))

        # Add transport DCs to the graph
        for n in self.dc_trans:
            self._add_node_to_graph(n, 'Trans', self.dc_share_cap_trans, self.dc_share_cost_trans, '#780000',
                                    latitude=random.uniform(40.2585977130845, 40.274018792148),
                                    longitude=random.uniform(-3.766972, -3.7423032373))

        # Add core DCs to the graph
        for n in self.dc_core:
            self._add_node_to_graph(n, 'Core', self.dc_share_cap_core, self.dc_share_cost_core, '#787000',
                                    latitude=random.uniform(40.2647663628264, 40.2674002969022),
                                    longitude=random.uniform(-3.75721197590123, -3.75380601283906))

    def generate_topology(self, path_to_the_topology, topology_size):

        self.graph = nx.DiGraph(name='MNO Architecture')
        self.graph.clear()

        # Generate separate lists for DCs in each level (edge, transport, core)
        self.dc_edge = ['dc_edge' + str(n) for n in range(1, self.num_dc_edge + 1)]
        self.dc_trans = ['dc_tran' + str(n) for n in range(1, self.num_dc_trans + 1)]
        self.dc_core = ['dc_core' + str(n) for n in range(1, self.num_dc_core + 1)]

        # Add edge DCs to the graph
        self._add_nodes_to_graph()

        # Generate separate lists for links in each level (Xn, fh, bh, inter_trans)
        self.e_xn = self._create_links(self.dc_edge, self.dc_edge)
        self.e_fh = self._create_links(self.dc_edge, self.dc_trans)
        self.e_trans = self._create_links(self.dc_trans, self.dc_trans)
        self.e_bh = self._create_links(self.dc_trans, self.dc_core, True)
        for n in self.dc_edge + self.dc_trans + self.dc_core:
            self.e_self_links.add((n, n))
        self.e = self.e_xn | self.e_fh | self.e_trans | self.e_bh | self.e_self_links

        # Add links to the graph
        self._add_links_to_graph()

        try:
            nx.write_gml(self.graph, _get_abs_location(path_to_the_topology, topology_size))
        except FileNotFoundError:
            error_message('The given path for storing the topology does not exist.')

    def load_config_data(self):
        # Numbers
        self.num_dc_edge = nc.number_of_dc_edge
        self.num_dc_trans = nc.number_of_dc_trans
        self.num_dc_core = nc.number_of_dc_core

        # Capacity
        self.dc_share_cap_edge = nc.dc_share_cap_edge
        self.dc_share_cap_trans = nc.dc_share_cap_trans
        self.dc_share_cap_core = nc.dc_share_cap_core

        self.link_share_cap_inDC = nc.link_share_cap_inDC
        self.link_share_cap_xn = nc.link_share_cap_xn
        self.link_share_cap_tr = nc.link_share_cap_tr
        self.link_share_cap_fh = nc.link_share_cap_fh
        self.link_share_cap_bh = nc.link_share_cap_bh

        # Cost
        self.dc_share_cost_edge = nc.dc_share_cost_edge
        self.dc_share_cost_trans = nc.dc_share_cost_trans
        self.dc_share_cost_core = nc.dc_share_cost_core

        self.link_share_cost_inDC = nc.link_share_cost_inDC
        self.link_share_cost_xn = nc.link_share_cost_xn
        self.link_share_cost_tr = nc.link_share_cost_tr
        self.link_share_cost_fh = nc.link_share_cost_fh
        self.link_share_cost_bh = nc.link_share_cost_bh

    def request_handler(self, topology_source):

        if topology_source == 'generate':
            self.load_config_data()
            self.generate_topology(nc.path_to_the_topology, nc.topology_name)
            self.draw()

        else:  # load topology from a file
            self.load_topology_from_file(nc.path_to_the_topology, nc.topology_name)
            self.draw()

        return self.graph, self.dc_edge

