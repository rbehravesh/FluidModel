"""
Generate or load the physical topology
"""

import copy
import time
import networkx as nx
import random
import network_config as nc
from layout import Style as style


class Topology:
    """
    Generate or load a network topology based on the given size
    """
    BIG_NUMBER = 999999999

    def __init__(self):
        self.graph = None
        self.dc_edge = set()
        self.dc_trans = set()
        self.dc_core = set()
        self.e_xn = set()
        self.e_fh = set()
        self.e_trans = set()
        self.e_bh = set()
        self.e_self_links = set()
        self.e = set()

    def request_handler(self, topology_source):

        if topology_source == 'generate':
            self.generate_topology(nc.path_to_the_topology, nc.topology_name)
            self.draw()
        else:
            self.load_topology_from_file(nc.path_to_the_topology, nc.topology_name)
            self.draw()

        return self.graph, self.dc_edge

    def draw(self):
        temp_graph = copy.deepcopy(self.graph)
        for n in temp_graph.nodes:
            temp_graph.remove_edge(n, n)

        colors = [n[1] for n in temp_graph.nodes(data="nodeColor")]
        try:
            nx.draw(temp_graph, with_labels=True, edge_color="gray", style="solid", node_size=450, font_size=11, width=2,
                    node_color=colors, alpha=1, arrowsize=12, arrowstyle='->',
                    labels={node: node[7:] for node in temp_graph.nodes()})
        except ValueError as e:
            self.error_message('Your topology file (.gml) is corrupted and cannot be drawn.'
                               ' Please refer to the below ERROR and fix the topology file.', e)

        import pylab as plt
        plt.savefig('plotgraph.png', dpi=1200, bbox_inches='tight')

    def _get_abs_location(self, path_to_the_topology, topology_size):
        return '{}{}_topology.gml'.format(path_to_the_topology, topology_size)

    def _get_detailed_topology(self):
        """
        Prepare the topology and store the details of the topology into different sets/variables and return them
        """
        # store the physical nodes (datacenters) in their respective variables
        for n in self.graph.nodes():
            if 'edge' in n:
                self.dc_edge.add(n)
            elif 'tran' in n:
                self.dc_trans.add(n)
            else:
                self.dc_core.add(n)

        # store the physical links in their respective variables
        for m, n in self.graph.edges():
            if m == n:
                self.e_self_links.add((m, n))
            elif m in self.dc_edge and n in self.dc_edge and m != n:
                self.e_xn.add((m, n))
            elif (m in self.dc_edge and n in self.dc_trans) or (m in self.dc_trans and n in self.dc_edge):
                self.e_fh.add((m, n))
            elif m in self.dc_trans and n in self.dc_trans and m != n:
                self.e_trans.add((m, n))
            elif (m in self.dc_core and n in self.dc_trans) or (m in self.dc_trans and n in self.dc_core):
                self.e_bh.add((m, n))

        # store nodes features into variables
        for n in self.dc_edge:
            self.dc_share_cap_edge = self.graph.nodes[n]['shareCap']
            self.dc_share_cost_edge = self.graph.nodes[n]['shareCost']
        for n in self.dc_trans:
            self.dc_share_cap_trans = self.graph.nodes[n]['shareCap']
            self.dc_share_cost_trans = self.graph.nodes[n]['shareCost']
        for n in self.dc_core:
            self.dc_share_cap_core = self.graph.nodes[n]['shareCap']
            self.dc_share_cost_core = self.graph.nodes[n]['shareCost']

        # store links features into variables
        for e in self.e_xn:
            self.link_share_cap_xn = self.graph.edges[e]['shareCap']
            self.link_share_cost_xn = self.graph.edges[e]['shareCost']
        for e in self.e_fh:
            self.link_share_cap_fh = self.graph.edges[e]['shareCap']
            self.link_share_cost_fh = self.graph.edges[e]['shareCost']
        for e in self.e_trans:
            self.link_share_cap_tr = self.graph.edges[e]['shareCap']
            self.link_share_cost_tr = self.graph.edges[e]['shareCost']
        for e in self.e_bh:
            self.link_share_cap_bh = self.graph.edges[e]['shareCap']
            self.link_share_cost_bh = self.graph.edges[e]['shareCost']

    def load_topology_from_file(self, path_to_the_topology, topology_size):
        try:
            self.graph = nx.read_gml(self._get_abs_location(path_to_the_topology, topology_size))
            self._get_detailed_topology()
        except FileNotFoundError as e:
            self.error_message('The given path or the file name for loading the topology does not exist.', e, True)
        except KeyError as e:
            self.error_message('There is a key error in the topology file. \nKey: ', e, True)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    """
    Generating a new topology based on the parameters given in network_config.py file
    """
    def _generate_nodes(self, size, node_type):
        return {node_type + str(n) for n in range(1, size + 1)}

    def _generate_links(self, first_set, second_set, isbh=False):
        links = set()
        for n in first_set:
            dist = Topology.BIG_NUMBER
            candidate = None
            for m in second_set:
                if m != n:
                    if self.get_distance_from_lat_lon_in_meter((self.graph.nodes[m]['lat'], self.graph.nodes[m]['lon']),
                            (self.graph.nodes[n]['lat'], self.graph.nodes[n]['lon'])) < dist:
                        dist = self.get_distance_from_lat_lon_in_meter((self.graph.nodes[m]['lat'], self.graph.nodes[m]['lon']),
                            (self.graph.nodes[n]['lat'], self.graph.nodes[n]['lon']))
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

    def _add_nodes_to_graph(self):
        self.graph.add_nodes_from(
            self.dc_edge, lat=None, lon=None, nodeColor='#7870b4', shareCap=nc.dc_share_cap_edge,
            shareCost=nc.dc_share_cost_edge, label='Edge Nodes')
        self.graph.add_nodes_from(
            self.dc_trans, lat=None, lon=None, nodeColor='#780000', shareCap=nc.dc_share_cap_trans,
            shareCost=nc.dc_share_cost_trans, label='Transport Nodes')
        self.graph.add_nodes_from(
            self.dc_core, lat=None, lon=None, nodeColor='#787000', shareCap=nc.dc_share_cap_core,
            shareCost=nc.dc_share_cost_core, label='Core Nodes')

    def _add_links_to_graph(self):
        if len(self.e):
            self.graph.add_edges_from((m, n, {'distance': 0, 'shareCap': 0, 'shareCost': 0, 'latency': 0})
                                      for m, n in self.e)
        # set features for the links
        for e in self.graph.edges:

            self.graph.edges[e]['distance'] = self.get_distance_from_lat_lon_in_meter(
                (self.graph.nodes[e[0]]['lat'], self.graph.nodes[e[0]]['lon']),
                 (self.graph.nodes[e[1]]['lat'], self.graph.nodes[e[1]]['lon']))
            self.graph.edges[e]['latency'] = self.graph.edges[e]['distance']

            if e[0] == e[1]:  # intra-DC links
                self.graph.edges[e]['latency'] = 0
                self.graph.edges[e]['shareCap'] = nc.link_share_cap_inDC
                self.graph.edges[e]['shareCost'] = nc.link_share_cost_inDC
            elif e in self.e_xn:
                self.graph.edges[e]['shareCap'] = nc.link_share_cap_xn
                self.graph.edges[e]['shareCost'] = nc.link_share_cost_xn
            elif e in self.e_trans:
                self.graph.edges[e]['shareCap'] = nc.link_share_cap_tr
                self.graph.edges[e]['shareCost'] = nc.link_share_cost_tr
            elif e in self.e_fh:
                self.graph.edges[e]['shareCap'] = nc.link_share_cap_fh
                self.graph.edges[e]['shareCost'] = nc.link_share_cost_fh
            elif e in self.e_bh:
                self.graph.edges[e]['shareCap'] = nc.link_share_cap_bh
                self.graph.edges[e]['shareCost'] = nc.link_share_cost_bh

    def get_distance_from_lat_lon_in_meter(self, m, n):
        from math import cos, asin, sqrt, pi
        lat1 = m[0]
        lon1 = m[1]
        lat2 = n[0]
        lon2 = n[1]

        p = pi / 180
        a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
        return (12742 * asin(sqrt(a))) * 1000  # 2*R*asin

    def _set_position_for_nodes_lat_lon(self):
        # set latitude and longitude for the nodes
        for n in self.dc_edge:
            self.graph.nodes[n]['lat'] = random.uniform(40.253602, 40.27668)
            self.graph.nodes[n]['lon'] = random.uniform(-3.77504, -3.737746)

        for n in self.dc_trans:
            self.graph.nodes[n]['lat'] = random.uniform(40.2585977130845, 40.274018792148)
            self.graph.nodes[n]['lon'] = random.uniform(-3.766972, -3.7423032373)

        for n in self.dc_core:
            self.graph.nodes[n]['lat'] = random.uniform(40.2647663628264, 40.2674002969022)
            self.graph.nodes[n]['lon'] = random.uniform(-3.75721197590123, -3.75380601283906)

    def generate_topology(self, path_to_the_topology, topology_size):
        self.dc_edge = self._generate_nodes(nc.number_of_dc_edge, 'dc_edge')
        self.dc_trans = self._generate_nodes(nc.number_of_dc_trans, 'dc_tran')
        self.dc_core = self._generate_nodes(nc.number_of_dc_core, 'dc_core')

        # Network graph (adding nodes to the graph)
        self.graph = nx.DiGraph(name='MNO Architecture')
        self.graph.clear()
        self._add_nodes_to_graph()
        self._set_position_for_nodes_lat_lon()

        # Network graph (adding links)
        self.e_xn = self._generate_links(self.dc_edge, self.dc_edge)
        self.e_fh = self._generate_links(self.dc_edge, self.dc_trans)
        self.e_trans = self._generate_links(self.dc_trans, self.dc_trans)
        self.e_bh = self._generate_links(self.dc_trans, self.dc_core, True)
        for n in self.dc_edge | self.dc_trans | self.dc_core:
            self.e_self_links.add((n, n))

        self.e = self.e_xn | self.e_fh | self.e_trans | self.e_bh | self.e_self_links

        self._add_links_to_graph()

        self._get_detailed_topology()

        try:
            nx.write_gml(self.graph, self._get_abs_location(path_to_the_topology, topology_size))
        except FileNotFoundError:
            self.error_message('The given path for storing the topology does not exist.')

    def get_info(self):
        print(f'...............\n'
              f'{style.BOLD}{style.YELLOW}Substrate Network Detailed Information:{style.END}\n'
              '...............')
        print(f'{style.BOLD}{style.DARKCYAN}Datacenters info:{style.END}')
        print(f'Edge Datacenters: {len(self.dc_edge)}, there are {self.dc_share_cap_edge} '
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

    def error_message(self, msg, e=None, finish=False, ):
        print(msg)
        print(style.RED, e, style.END)
        if finish:
            print('The execution is ending...')
            time.sleep(5)
            exit(0)
