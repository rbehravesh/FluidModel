""""
Second phase of the service embedding -- per user allocation
"""

from operator import attrgetter

from vEntities import Function
from vEntities import Link
from gurobipy import *
from layout import Style as style


def per_user_allocation_heuristic(model, direct, transient, applications, graph, users):
    """
    Perform per user allocation of computing shares

    :param model: the model received from the Fluid (Linear Program) model
    :param direct: 'direct' variable received from the Fluid Model
    :param transient: 'transient' variable received from the Fluid Model
    :param applications: list of exact applications requested by the users
    :param graph: physical network (substrate network) topology
    :param users: list of all users that make service requests
    :return: prints per user allocation of resources
    """

    # Define temp variables for storing LP variables, their values and cost
    direct_tmp, transient_tmp = define_temp_variables(direct, transient, applications, graph)

    direct_heu, shares_direct, cost_direct = multidict({
        (a, s, i, j, m, n): [shares, cost] for a, s, i, j, m, n, shares, cost in direct_tmp})

    transient_heu, shares_transient, cost_transient = multidict({
        (a, s, i, j, m, n): [shares, cost] for a, s, i, j, m, n, shares, cost in transient_tmp})

    direct_allocation, transient_allocation = initialize_decision_variables(direct_tmp, transient_tmp, users)

    del transient_tmp, direct_tmp

    direct_allocation, transient_allocation, rejected_users = perform_allocation(
        users, applications, cost_direct, shares_direct, direct_allocation,
        cost_transient, shares_transient, transient_allocation)

    print(f'{style.YELLOW}{style.BOLD} \n******** Second stage of allocations'
          f' (Per-user allocation) ******** {style.END}')

    print_output('Direct', direct_allocation, applications)
    print_output('Transient', transient_allocation, applications)
    print_rejected_users(rejected_users)

    return [len(rejected_users)]


def ordered_selection_of_resources(variable, cost_variable, counter, i, j, next_s, next_m, a, shares_variable,
                                   allocation_variable, u, number_of_embedded_links, flag):
    """
    # Loop over the sorted direct links and consider each solution as an item for allocating to the user
    """
    for (item_a, item_s, item_i, item_j, item_m, item_n), val in \
            sorted(cost_variable.items(), key=lambda item: item[1], reverse=False):

        counter += 1
        if (item_a == a.name) and (item_i == i) and (item_j == j):
            if (item_s == next_s) and (item_m == next_m):
                if shares_variable[item_a, item_s, i, j, item_m, item_n] >= \
                        a.edges[i, j]['shareDemand'] * u.share_demand:

                    allocation_variable[u, item_a, item_s, i, j, item_m, item_n] = \
                        a.edges[i, j]['shareDemand'] * u.share_demand

                    shares_variable[a.name, item_s, i, j, item_m, item_n] -= \
                        a.edges[i, j]['shareDemand'] * u.share_demand

                    if variable == 'Direct':
                        number_of_embedded_links += 1
                        next_m = item_n
                        next_s = item_n
                        flag = True
                        break
                    elif variable == 'Transient':
                        next_m = item_n
                        counter = 0

    return [allocation_variable, counter, number_of_embedded_links, next_m, next_s, flag]


def perform_allocation(users, applications, cost_direct, shares_direct, direct_allocation,
                       cost_transient, shares_transient, transient_allocation):
    rejected_users = list()

    # for u in users:
    users_list = list(users)
    users_list.sort(key=attrgetter('share_demand'), reverse=True)
    for u in users_list:
        number_of_embedded_links = 0
        next_s = u.assoc_dc
        next_m = u.assoc_dc
        for a in (a for a in applications if u.app_demand.name == a.name):
            # number of embedded logical links for each user (all should be embedded; otherwise, user is Rejected)
            for i, j in a.edges():

                flag = False
                counter = 0
                while flag is False:
                    if counter >= len(direct_allocation) + len(transient_allocation):
                        flag = True
                        break

                    direct_allocation, counter, number_of_embedded_links, next_m, next_s, flag = \
                        ordered_selection_of_resources('Direct', cost_direct, counter, i, j, next_s,
                                                       next_m, a, shares_direct, direct_allocation,
                                                       u, number_of_embedded_links, flag)


                    if flag:  # a direct link has been found
                        break
                    else:
                        transient_allocation, counter, number_of_embedded_links, next_m, next_s, flag = \
                            ordered_selection_of_resources('Transient', cost_transient, counter, i, j, next_s,
                                                           next_m, a, shares_transient, transient_allocation, u,
                                                           number_of_embedded_links, flag)

                        continue

            # if none of the direct and transient solutions can be exploited for the user then it is REJECTED!
            if number_of_embedded_links < len(a.edges):
                rejected_users.append((a, u))
                # deallocate_resources(u, direct_allocation, transient_allocation, shares_direct, shares_transient)
                break

    return [direct_allocation, transient_allocation, rejected_users]


def deallocate_resources(u, direct_allocation, transient_allocation, shares_direct, shares_transient):
    for u_, a, s, i, j, m, n in direct_allocation:
        if u_ == u:
            direct_allocation[u, a, s, i, j, m, n] = 0
            shares_direct[a, s, i, j, m, n] += u.share_demand

    for u_, a, s, i, j, m, n in transient_allocation:
        if u_ == u:
            transient_allocation[u, a, s, i, j, m, n] = 0
            shares_transient[a, s, i, j, m, n] += u.share_demand


def define_temp_variables(direct, transient, applications, graph):
    """
    Store cost and amount of shares of each of the solutions of direct and transient links into dictionary
    :param direct:
    :param transient:
    :param applications:
    :param graph:
    :return: two temporary variables for direct and transient variables with their shares and cost of shares
    """
    direct_tmp = [['a', 's', 'i', 'j', 'm', 'n', 0, 0]]
    transient_tmp = [['a', 's', 'i', 'j', 'm', 'n', 0, 0]]

    # Store the direct and transient links with their associated share values and cost of the into temp variables
    for app, s, i, j, m, n in direct:
        for a in (a for a in applications if a.name == app):
            if direct[a.name, s, i, j, m, n].X:
                direct_tmp.append([a.name, s, i, j, m, n, direct[a.name, s, i, j, m, n].X,
                                   (graph.edges[(m, n)]['shareCost'] * Link(i, j).get_share_multiplier((m, n))
                                    * a.edges[(i, j)]['shareDemand'] + graph.nodes[n]['shareCost']
                                    * a.edges[i, j]['shareDemand'] * Function(j).get_share_multiplier(n))])

            if transient[a.name, s, i, j, m, n].X:
                transient_tmp.append([a.name, s, i, j, m, n, transient[a.name, s, i, j, m, n].X,
                                      (graph.edges[(m, n)]['shareCost'] * Link(i, j).get_share_multiplier((m, n)) *
                                       a.edges[(i, j)]['shareDemand'])])
    return [direct_tmp, transient_tmp]


def initialize_decision_variables(direct_tmp, transient_tmp, users):
    """
    Initialize decision variables of the heuristic method using two dictionaries and set their values to zero
    """

    direct_allocation = {}
    transient_allocation = {}
    for u in users:
        for a, s, i, j, m, n, _, _ in direct_tmp:
            if u.app_demand.name == a:
                direct_allocation[u, a, s, i, j, m, n] = 0

        for a, s, i, j, m, n, _, _ in transient_tmp:
            if u.app_demand.name == a:
                transient_allocation[u, a, s, i, j, m, n] = 0

    return [direct_allocation, transient_allocation]


def print_output(variable_name, variable, applications):
    total_shares_alloc = 0
    for a in applications:
        for u, app, s, i, j, m, n in variable:
            if app == a.name:
                if variable.get((u, app, s, i, j, m, n)):
                    value = Function(j).get_share_multiplier(n) * a.edges[i, j]['shareDemand']\
                             * variable.get((u, app, s, i, j, m, n))

                    if value == 0:
                        print(variable_name, ':', u.id_, a.name, s, i, j, m, n, '----> ',
                              variable[u, a.name, s, i, j, m, n], style.BOLD, style.GREEN,
                              '(it is embedded but it does not affect the actual consumed capacity)', style.END)
                    else:
                        print(variable_name, ':', u.id_, a.name, s, i, j, m, n, '----> ', Function(j).get_share_multiplier(n) *
                              a.edges[i, j]['shareDemand'] * variable[u, a.name, s, i, j, m, n])
                        total_shares_alloc += variable[u, a.name, s, i, j, m, n]

    print(f'{style.PURPLE}{style.UNDERLINE}Total allocated (consumed capacity) shares to the {variable_name} links is: '
          f'{float(total_shares_alloc)}{style.END}')


def print_rejected_users(rejected_users):
    if not len(rejected_users):
        print(style.BOLD, style.BLUE, 'All the users are embedded successfully!', style.END)
    for a, u in rejected_users:
        print('Application ', a, 'of user ', u.id_, 'cannot be embedded fully!', style.RED, 'REJECTED!',
              style.END)