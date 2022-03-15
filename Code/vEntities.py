"""
Virtual Entities Classes (Users, Applications, Functions)
"""

import random
import networkx as nx
import network_config as nc
import embedding
from layout import Style as style


class User:
    total_share_demand = 0

    def __init__(self, id_, dc_edge):
        self.id_ = 'u' + str(id_)
        self.share_demand = embedding.share_demand_normal[id_ - 1]
        User.total_share_demand += self.share_demand
        application = Application()
        self.app_demand = random.choice(application.get_app_list(nc.number_of_apps))
        # self.assoc_dc = 'dc_edge' + str(embedding.edge_dcs_zipf[id_ - 1])
        self.assoc_dc = 'dc_edge' + str(embedding.edge_dcs_uniform[id_ - 1])

    def get_share_demand_on_dc(self, d):
        if d == self.assoc_dc:
            return self.share_demand
        else:
            return 0

    def get_info(self):
        print('{}{}user:{} {} - {}{}share_demand:{} {} - {}{}app_demand:{} {} - {}{}assoc_dc:{} {}'
              .format(style.BLUE, style.BOLD, style.END, self.id_,
                      style.BLUE, style.BOLD, style.END, self.share_demand,
                      style.BLUE, style.BOLD, style.END, self.app_demand,
                      style.BLUE, style.BOLD, style.END, self.assoc_dc))

    @classmethod
    def group_users(cls, users, applications_list):
        """
        grouping of users that have the same application demand and they are associated to the same edge datacenter
        :param users: set of users that make service requests
        :param applications_list: list of all application that users can select from
        :return: a set of users that are grouped together based on having the same application demand an edge datacenter
        """
        users_with_same_app_and_edge = set()

        for a in applications_list:
            for u in users:
                if u.app_demand.name == a.name:
                    users_with_same_app_and_edge.add((a, u.assoc_dc))

        grouped_users = set()
        number_of_grouped_users = {i for i in range(1, len(users_with_same_app_and_edge) + 1)}
        for g_u, item in zip(number_of_grouped_users, users_with_same_app_and_edge):
            grouped_users.add(GroupUser(g_u, item[0], item[1]))

        for g_u in grouped_users:
            for u in users:
                if g_u.app_demand.name == u.app_demand.name and g_u.assoc_dc == u.assoc_dc:
                    g_u.share_demand += u.share_demand

        return list(grouped_users)

    @classmethod
    def get_info_all_users(cls, users):
        print(f'...............\n'
              f'{style.BOLD}{style.YELLOW}Users\' information:{style.END}\n'
              '...............')
        list_of_users = list(users)
        list_of_users.sort(key=lambda u: u.id_, reverse=False)
        for u in list_of_users:
            print('{}{}user:{} {} - {}{}share_demand:{} {} - {}{}app_demand:{} {} - {}{}assoc_dc:{} {}'
                  .format(style.BLUE, style.BOLD, style.END, u.id_,
                          style.BLUE, style.BOLD, style.END, u.share_demand,
                          style.BLUE, style.BOLD, style.END, u.app_demand,
                          style.BLUE, style.BOLD, style.END, u.assoc_dc))

        print(f'{style.PURPLE}{style.BOLD} Total share demand requested by the users: '
              f'{cls.total_share_demand}{style.END}')

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


class GroupUser(User):
    def __init__(self, id_, app_demand, assoc_dc, share_demand=0):
        self.id_ = 'g_u' + str(id_)
        self.app_demand = app_demand
        self.assoc_dc = assoc_dc
        self.share_demand = share_demand

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


class Application:
    """
    Define graph of the applications
    Note: in order to support more applications their graph should be first added hear and then change the number of
    applications in the configuration file
    """
    applications_list = list()

    def __init__(self):
        self.func_u = Function('U')
        self.func_t = Function('T')
        self.func_f = list()
        for n in range(nc.number_of_functions):
            self.func_f.append(Function('f' + str(n)))

        # Application graphs
        self.G_app1 = nx.DiGraph(name="a1")
        self.G_app1.add_edges_from([(Link(self.func_u, self.func_f[0]).get_link()),
                                    (Link(self.func_f[0], self.func_f[1]).get_link()),
                                    (Link(self.func_f[1], self.func_t).get_link())])

        self.G_app2 = nx.DiGraph(name="a2")
        self.G_app2.add_edges_from([(Link(self.func_u, self.func_f[1]).get_link()),
                                    (Link(self.func_f[1], self.func_f[2]).get_link()),
                                    (Link(self.func_f[1], self.func_f[3]).get_link()),
                                    (Link(self.func_f[2], self.func_t).get_link()),
                                    (Link(self.func_f[3], self.func_t).get_link())])

        self.G_app3 = nx.DiGraph(name="a3")
        self.G_app3.add_edges_from([(Link(self.func_u, self.func_f[0]).get_link()),
                                    (Link(self.func_f[0], self.func_f[1]).get_link()),
                                    (Link(self.func_f[0], self.func_f[2]).get_link()),
                                    (Link(self.func_f[0], self.func_f[3]).get_link()),
                                    (Link(self.func_f[1], self.func_t).get_link()),
                                    (Link(self.func_f[2], self.func_t).get_link()),
                                    (Link(self.func_f[3], self.func_t).get_link())])

        self.G_app4 = nx.DiGraph(name="a4")
        self.G_app4.add_edges_from([(Link(self.func_u, self.func_f[0]).get_link()),
                                    (Link(self.func_f[0], self.func_f[3]).get_link()),
                                    (Link(self.func_f[3], self.func_f[4]).get_link()),
                                    (Link(self.func_f[4], self.func_t).get_link())])

        self.G_app5 = nx.DiGraph(name="a5")
        self.G_app5.add_edges_from([(Link(self.func_u, self.func_f[0]).get_link()),
                                    (Link(self.func_f[0], self.func_f[3]).get_link()),
                                    (Link(self.func_f[0], self.func_f[4]).get_link()),
                                    (Link(self.func_f[4], self.func_f[5]).get_link()),
                                    (Link(self.func_f[3], self.func_t).get_link()),
                                    (Link(self.func_f[5], self.func_t).get_link())])
        self.number_of_apps = None

    def _set_feature_of_logical_links(self):
        for a in Application.applications_list:
            for i, j in a.edges():
                a.edges[(i, j)]['shareDemand'] = Link(i, j).share_demand
                a.edges[(i, j)]['latencyDemand'] = Link(i, j).latency_demand

    def _set_feature_of_logical_functions(self):
        for a in Application.applications_list:
            for i in a.nodes():
                a.nodes[i]['shareDemand'] = Function(i).share_demand

    def get_app_list(self, number_of_apps):
        self.number_of_apps = number_of_apps
        app_list = [self.G_app1, self.G_app2, self.G_app3, self.G_app4, self.G_app5]
        self._set_feature_of_logical_links()
        self._set_feature_of_logical_functions()
        Application.applications_list = app_list[:number_of_apps]
        return Application.applications_list

    @classmethod
    def get_aggregate_dc_demand(cls, a, grouped_users, d):
        """
        :returns the aggregate demand on a datacenter (demand from all the application)
        """
        aggregated_demand = 0
        for g_u in grouped_users:
            if g_u.app_demand == a:
                if g_u.assoc_dc == d:
                    aggregated_demand += g_u.share_demand
        return aggregated_demand

    @classmethod
    def get_aggregate_app_demand(cls, application, grouped_users):
        """
        :returns the aggregate demand for an application (total demand for an application)
        """
        aggregated_demand = 0
        for g_u in grouped_users:
            if g_u.app_demand.name == application.name:
                aggregated_demand += g_u.share_demand

        return aggregated_demand

    def get_info(self):
        apps = self.get_app_list(self.number_of_apps)
        print('...............\n'
              f'{style.BOLD}{style.YELLOW}Graph of the applications:{style.END}\n'
              '...............')
        for a in apps:
            print(a.name, a.edges())
        print('=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')


class Function:
    """
    define the features and functions on logical (virtual) functions
    """

    def __init__(self, id_):
        self.id_ = id_
        self.share_multiplier = 0
        self.share_demand = 1

    def get_share_multiplier(self, n):
        """
        share multiplier defines the weight of placing a function of a specific physical node
        :param n: the physical node
        :return: multiplier value for a given function on a physical node
        """
        # 'n' is given as parameter because this function can be modified to consider share_multiplier based on the node
        self.share_multiplier = 1
        if self.id_ == 'U' or self.id_ == 'T':
            self.share_multiplier = 0

        return self.share_multiplier

    def get_info(self):
        return 'function: {} - share_multiplier: {}'\
            .format(self.id_, self.share_multiplier)


class Link:
    """
    Defines the features and methods on logical (virtual) links
    """
    def __init__(self, source_function, target_function):
        self.source_function = source_function
        self.target_function = target_function
        self.share_multiplier = 1
        self.latency_demand = 100000  # todo This numbers can change for latency eval.
        self.share_demand = 1  # mapping of 1 EUC requested by users is equal to 1 share of each link (can be changed)
        # if self.target_function == 'T':
        #     self.share_demand = 0

    # share multiplier of a logical link on a physical link
    def get_share_multiplier(self, e):
        """
        share multiplier defines the weight of placing a link of a specific physical link
        :param e: the physical link between nodes (m, n)
        :return: multiplier value for the given logical link on a physical link
        """
        self.share_multiplier = 1
        if self.target_function == 'T':
            self.share_multiplier = 0
        if e[0] == e[1]:
            self.share_multiplier = 0

        return self.share_multiplier

    def get_link(self):
        return self.source_function.id_, self.target_function.id_
