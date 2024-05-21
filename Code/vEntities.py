"""
Virtual Entities Classes (Users, Applications, Functions)
"""
import networkx as nx
from layout import Style as style


class User:

    def __init__(self, id_, app_demand, share_demand, edge_assoc):
        self.id_ = f'u{id_ + 1}'
        self.app_demand = app_demand.graph
        self.share_demand = share_demand
        self.assoc_dc = f'dc_edge{edge_assoc}'

    @classmethod
    def group_users(cls, users_list, applications_list, dc_edge):
        """
        Group users that have the same application demand and are associated to the same edge datacenter.
        """
        app_edge_combinations = {(app.graph, d): {'users': [], 'total_demand': 0}
                                 for app in applications_list for d in dc_edge}

        for user in users_list:
            key = (user.app_demand, user.assoc_dc)
            app_edge_combinations[key]['users'].append(user.id_)
            app_edge_combinations[key]['total_demand'] += user.share_demand

        grouped_users = [GroupUser(u + 1, app_demand_obj, assoc_dc, data['total_demand'])
                         for u, ((app_demand_obj, assoc_dc), data) in enumerate(app_edge_combinations.items())
                         if data['total_demand'] > 0]

        return grouped_users


class GroupUser(User):
    def __init__(self, id_, app_demand, assoc_dc, share_demand):
        super().__init__(id_, app_demand, share_demand, assoc_dc)
        self.id_ = id_
        self.app_demand = app_demand

def print_users_information(users_list):
    """
    Print detailed information about each user.
    """
    print(f'...............\n{style.BOLD}{style.YELLOW}Users\' information:{style.END}\n...............')
    total_app_share_demand = sum(user.share_demand for user in users_list)
    total_functions_share_demand = sum(user.share_demand * (len(user.app_demand.nodes()) - 2) for user in users_list)

    for user in sorted(users_list, key=lambda u: u.id_):
        print(f"{style.BLUE}{style.BOLD}user:{style.END} {user.id_} - "
              f"{style.BLUE}{style.BOLD}share_demand:{style.END} {user.share_demand} - "
              f"{style.BLUE}{style.BOLD}app_demand:{style.END} {user.app_demand} - "
              f"{style.BLUE}{style.BOLD}assoc_dc:{style.END} {user.assoc_dc}")

    print(f'{style.PURPLE}{style.BOLD}Total application share demands requested by users: '
          f'{total_app_share_demand}{style.END}\n'
          f'{style.BOLD}{style.GREEN}Total actual share demand (app share demand x num. app functions): '
          f'{total_functions_share_demand}{style.END}')


def set_functions_attributes(app_graph):
    """
    Set attributes for functions in an application graph.
    """
    for f in app_graph.nodes():
        app_graph.nodes[f]['isSplitter'] = False
        app_graph.nodes[f]['shareMultiplier'] = 0 if f in ('U', 'T') else 1


def set_links_attributes(app_graph):
    """
    Set attributes for links in an application graph.
    """
    latency_demand = 10 * 10**9  # Default latency demand, change as needed
    for i, j in app_graph.edges():
        app_graph.edges[(i, j)]['shareMultiplier'] = 0 if j == 'T' else 1
        app_graph.edges[(i, j)]['latencyDemand'] = 0 if j == 'T' else latency_demand


class Application:
    def __init__(self, app_id):
        self.graph = nx.DiGraph(name=f'App{app_id}')
        self._construct_graph()
        set_functions_attributes(self.graph)
        set_links_attributes(self.graph)

    def _construct_graph(self):
        """
        Construct the graph of the application based on its name.
        """
        edges = {
            'App1': [('U', 'f1'), ('f1', 'f2'), ('f2', 'f3'), ('f3', 'f4'), ('f4', 'T')],
            'App2': [('U', 'f1'), ('f1', 'f2'), ('f2', 'f3'), ('f2', 'f4'), ('f3', 'T'), ('f4', 'T')],
            'App3': [('U', 'f1'), ('f1', 'f2'), ('f1', 'f3'), ('f1', 'f4'), ('f2', 'T'), ('f3', 'T'), ('f4', 'T')],
            'App4': [('U', 'f1'), ('f1', 'f4'), ('f4', 'f5'), ('f5', 'T')],
            'App5': [('U', 'f1'), ('f1', 'f4'), ('f1', 'f5'), ('f5', 'f6'), ('f4', 'T'), ('f6', 'T')]
        }
        self.graph.add_edges_from(edges.get(self.graph.name, []))


def get_aggregate_dc_demand(app, grouped_users, dc):
    """
    Calculate the aggregate demand on a datacenter for a given application.
    """
    return sum(g_u.share_demand for g_u in grouped_users if g_u.app_demand.name == app.name and g_u.assoc_dc == dc)
