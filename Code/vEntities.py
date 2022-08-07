"""
Virtual Entities Classes (Users, Applications, Functions)
"""
import networkx as nx
from layout import Style as style


class User:
    total_users_share_demand = 0
    total_apps_share_demand = 0

    def __init__(self, id_, app_demand, share_demand, edge_assoc):
        self.id_ = 'u' + str(id_ + 1)
        self.app_demand = app_demand.graph
        self.share_demand = share_demand
        self.assoc_dc = 'dc_edge' + str(edge_assoc)

        User.total_users_share_demand += self.share_demand
        User.total_apps_share_demand += self.share_demand * (len(self.app_demand.edges) - 2)

    @classmethod
    def group_users(cls, users_list, applications_list, dc_edge):
        """
        grouping of users that have the same application demand and they are associated to the same edge datacenter
        :param dc_edge:
        :param users_list: set of users that make service requests
        :param applications_list: list of all application that users can select from
        :return: (aggregated demand) of a set of users that are grouped together based on having the same application demand an edge datacenter
        """
        combination_of_apps_edges = {(app.graph, d): [[], 0]
                                     for app in applications_list
                                     for d in dc_edge}

        num_uniq_agg_demands = 0
        for u in users_list:
            # list of users on a dc that demand same app
            combination_of_apps_edges.get((u.app_demand, u.assoc_dc))[0].append(u.id_)
            # amount of shares on a dc for an app
            combination_of_apps_edges.get((u.app_demand, u.assoc_dc))[1] += u.share_demand
            num_uniq_agg_demands += 1

        g_u_id = 1
        grouped_users_list = []
        for app_demand, assoc_dc in combination_of_apps_edges:
            share_demand = combination_of_apps_edges.get((app_demand, assoc_dc))[1]
            if share_demand > 0:
                grouped_users_list.append(GroupUser(g_u_id, app_demand, assoc_dc, share_demand))
                g_u_id += 1

        return grouped_users_list


def print_users_information(users_list):
    print(f'...............\n'
          f'{style.BOLD}{style.YELLOW}Users\' information:{style.END}\n'
          '...............')
    total_app_share_demand = 0
    total_functions_share_demand = 0
    for u in sorted(users_list, key=lambda u: u.id_, reverse=False):
        total_app_share_demand += u.share_demand
        total_functions_share_demand += u.share_demand * (len(u.app_demand.nodes()) - 2) #
        print('{}{}user:{} {} - {}{}share_demand:{} {} - {}{}app_demand:{} {} - {}{}assoc_dc:{} {}'
              .format(style.BLUE, style.BOLD, style.END, u.id_,
                      style.BLUE, style.BOLD, style.END, u.share_demand,
                      style.BLUE, style.BOLD, style.END, u.app_demand,
                      style.BLUE, style.BOLD, style.END, u.assoc_dc))

    print(f'{style.PURPLE}{style.BOLD}Total application share demands requested by users: '
          f'{total_app_share_demand} {style.END}{style.BOLD}{style.GREEN}\n'
          f'Total actual share demand (app share demand x num. app functions): '
          f'{total_functions_share_demand}{style.END}')


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


class GroupUser(User):
    def __init__(self, id_, app_demand, assoc_dc, share_demand):
        self.id_ = 'g_u' + str(id_)
        self.app_demand = app_demand
        self.assoc_dc = assoc_dc
        self.share_demand = share_demand


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


def set_functions_attributes(G_app):
    for f in G_app.nodes():
        G_app.nodes[f]['isSplitter'] = False
        if f == 'U' or f == 'T':
            G_app.nodes[f]['shareMultiplier'] = 0
        else:
            G_app.nodes[f]['shareMultiplier'] = 1


def set_links_attributes(G_app):
    for i, j in G_app.edges():
        G_app.edges[(i, j)]['shareMultiplier'] = 1
        G_app.edges[(i, j)]['latencyDemand'] = 10**10  # todo change
        if j == 'T':
            G_app.edges[(i, j)]['shareMultiplier'] = 0
            G_app.edges[(i, j)]['latencyDemand'] = 0


class Application:
    """
    Define graph of the applications
    Note: in order to support more applications their graph should be first added hear and then change the number of
    applications in the configuration file
    """

    def __init__(self, app_id):
        # Application graphs
        self.graph = nx.DiGraph(name='App' + str(app_id))

        if self.graph.name == 'App1':
            self.graph.add_edges_from([('U', 'f1'), ('f1', 'f2'), ('f2', 'f3'), ('f3', 'f4'), ('f4', 'T')])
            # self.graph.add_edges_from([  #todo: use this for the case of having a splitter function
            #     ('U', 'f1'), ('f1', 'f2_a'), ('f2_a', 'T'), ('f1', 'c'), ('c', 'f2_b'), ('f2_b', 'T')
            # ])
            # self.graph.nodes['f1']['isSplitter'] = True

        elif self.graph.name == 'App2':
            self.graph.add_edges_from([('U', 'f1'), ('f1', 'f2'), ('f2', 'f3'), ('f2', 'f4'), ('f3', 'T'), ('f4', 'T')])
        elif self.graph.name == 'App3':
            self.graph.add_edges_from([('U', 'f1'), ('f1', 'f2'), ('f1', 'f3'), ('f1', 'f4'), ('f2', 'T'), ('f3', 'T'),
                                       ('f4', 'T')])
        elif self.graph.name == 'App4':
            self.graph.add_edges_from([('U', 'f1'), ('f1', 'f4'), ('f4', 'f5'), ('f5', 'T')])
        elif self.graph.name == 'App5':
            self.graph.add_edges_from([('U', 'f1'), ('f1', 'f4'), ('f1', 'f5'), ('f5', 'f6'), ('f4', 'T'), ('f6', 'T')])

        # Assign features to the functions in the application
        set_functions_attributes(self.graph)

        # Assign features to the logical links in the application
        set_links_attributes(self.graph)


def get_aggregate_dc_demand(app, grouped_users, dc):
    """
    returns the aggregate demand on a datacenter
    """
    aggregated_demand = 0
    for g_u in grouped_users:
        if g_u.app_demand.name == app.name:
            if g_u.assoc_dc == dc:
                aggregated_demand += g_u.share_demand
    return aggregated_demand
