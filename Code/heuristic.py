import math
import timeit

from layout import Style as style


def get_value_of_valid_directs(direct, graph):
    valid_directs = {}
    for a, s, i, j, m, n in direct:
        cost = (graph.edges[(m, n)]['shareCost'] * a.edges[(i, j)]['shareMultiplier']
                + graph.nodes[n]['shareCost'] * a.nodes[j]['shareMultiplier'])

        shares = direct[a, s, i, j, m, n].X
        if shares <= 0:
            continue

        valid_directs.setdefault((a, s, i, j, m), []).append((n, shares, cost))

    # Sort valid_direct by the cost
    for l in valid_directs.values():
        l.sort(key=lambda item: item[2], reverse=False)

    return valid_directs


def get_value_of_valid_transients(transient, graph):
    valid_transients = {}
    for a, s, i, j, m, n in transient:
        cost = (graph.edges[(m, n)]['shareCost'] * a.edges[(i, j)]['shareMultiplier'])

        shares = transient[a, s, i, j, m, n].X
        if shares <= 0:
            continue

        valid_transients.setdefault((a, s, i, j, m), []).append((n, shares, cost))

    # Sort valid_transient by the cost
    for l in valid_transients.values():
        l.sort(key=lambda item: item[2], reverse=False)

    return valid_transients


def per_user_allocation_heuristic(model, direct, transient, graph, users, fictitious_dcs=None):
    """
    Perform per user allocation of computing shares
    """
    print(f'{style.YELLOW}{style.BOLD} \n******** Second stage of allocations'
          f' (Per-user allocation) ******** {style.END}')

    run_time_start = timeit.default_timer()
    # A dict for storing the direct shares computed from the LP model
    valid_directs = get_value_of_valid_directs(direct, graph)

    # A dict for storing the transient shares computed from the LP model
    valid_transients = get_value_of_valid_transients(transient, graph)

    # new decision variables to store per-user allocations

    rejected_users, share_amount_rejected, num_users_on_fictitious, share_amount_on_fictitious = \
        perform_allocation(users, valid_directs, valid_transients, fictitious_dcs)

    print_rejected_users(rejected_users, share_amount_rejected, num_users_on_fictitious, share_amount_on_fictitious, 'Fluid Summary')

    run_time_stop = timeit.default_timer()
    exec_time_heu = run_time_stop - run_time_start

    return [len(rejected_users), share_amount_rejected, num_users_on_fictitious, share_amount_on_fictitious, exec_time_heu]


def find_next_hop(variable_name, i, j, s, m, a, valid_shares, u, allocation_variable):
    """
    # Loop over the sorted direct links and consider each solution as an item for allocating to the user
    """

    possible_next_hops = valid_shares.get((a, s, i, j, m), [])

    for k in range(len(possible_next_hops) - 1, -1, -1):
        n, shares, cost = possible_next_hops[k]

        if math.ceil(shares) >= u.share_demand:
            allocation_variable[u, a, s, i, j, m, n] = u.share_demand
            shares -= u.share_demand

            if shares <= 0:
                del possible_next_hops[k]
            else:
                possible_next_hops[k] = (n, shares, cost)

            if variable_name == 'Direct':
                s = n

            return [n, s, True]

    return [m, s, False]


def perform_allocation(users, valid_directs, valid_transients, fictitious_dcs):

    rejected_users = list()
    share_amount_rejected = 0
    share_amount_on_fictitious = 0
    users_on_fictitious = set()

    for u in users:
        # print(f'{style.YELLOW}--------------------------------------------{style.END}')
        direct_allocation = {}
        transient_allocation = {}

        next_s = u.assoc_dc
        next_m = u.assoc_dc

        # Number of embedded logical links for each user (all should be embedded; otherwise, user is Rejected)
        for i, j in u.app_demand.edges():  # returns edges in BFS order
            not_rejected_yet = True
            while not_rejected_yet:
                next_m, next_s, not_rejected_yet = find_next_hop('Direct', i, j, next_s, next_m, u.app_demand, valid_directs,
                                                                 u, direct_allocation)
                if not_rejected_yet:  # a direct link has been found
                    break

                next_m, next_s, not_rejected_yet = find_next_hop('Transient', i, j, next_s, next_m, u.app_demand, valid_transients,
                                                                 u, transient_allocation)

            # if it failed in embedding the
            if not not_rejected_yet:
                rejected_users.append((u.app_demand, u))
                share_amount_rejected += u.share_demand
                # deallocate_resources(u, direct_allocation, transient_allocation, shares_direct, shares_transient)
                break

        # print_output('Direct', direct_allocation)
        # print_output('Transient', transient_allocation)

        # Find users that are mapped on the fictitious DC
        if fictitious_dcs is not None:
            for u_, a, s, i, j, m, n in direct_allocation:
                if direct_allocation[u_, a, s, i, j, m, n] and n.startswith('fic'):
                    users_on_fictitious.add(u_)

    share_amount_on_fictitious += sum((u.share_demand for u in users_on_fictitious))

    return rejected_users, share_amount_rejected, len(users_on_fictitious), share_amount_on_fictitious


def deallocate_resources(u, direct_allocation, transient_allocation, shares_direct, shares_transient):
    for u_, a, s, i, j, m, n in direct_allocation:
        if u_ == u:
            direct_allocation[u, a, s, i, j, m, n] = 0
            shares_direct[a, s, i, j, m, n] += u.share_demand

    for u_, a, s, i, j, m, n in transient_allocation:
        if u_ == u:
            transient_allocation[u, a, s, i, j, m, n] = 0
            shares_transient[a, s, i, j, m, n] += u.share_demand


def print_output(variable_name, variable):
    total_shares_alloc = 0
    for u, a, s, i, j, m, n in variable:
        if variable.get((u, a, s, i, j, m, n)):
            value = a.edges[i, j]['shareMultiplier'] * variable.get((u, a, s, i, j, m, n))

            if value == 0:
                print(variable_name, ':', u.id_, a.name, s, i, j, m, n, '----> ',
                      variable[u, a, s, i, j, m, n], style.BOLD, style.GREEN,
                      '(No effect on the actual consumed capacity)', style.END)
            else:
                print(variable_name, ':', u.id_, a.name, s, i, j, m, n, '----> ',
                      a.edges[i, j]['shareMultiplier'] * variable[u, a, s, i, j, m, n])
                total_shares_alloc += variable[u, a, s, i, j, m, n]


def print_rejected_users(rejected_users, share_amount_rejected, num_users_on_fictitious, share_amount_on_fictitious, key):
    print('------------------------------------------------------------------\n', style.BOLD, key, style.END)
    if not len(rejected_users) + num_users_on_fictitious:
        print(style.BOLD, style.BLUE, 'All users are embedded successfully for Fluid!', style.END)

    print(style.BLUE, '# of users that FAILED to be embedded by the algorithm:', style.END, len(rejected_users))
    print(style.BLUE, 'Total share demand that FAILED to be embedded by the algorithm:', style.END, share_amount_rejected)

    print(style.PURPLE, '# of users that ended up at a Fictitious DC: ', style.END, num_users_on_fictitious)
    print(style.PURPLE, 'User share amount ended up at a Fictitious DC: ', style.END, share_amount_on_fictitious)
    print('------------------------------------------------------------------')
