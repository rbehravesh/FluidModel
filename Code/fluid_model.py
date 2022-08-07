"""
 First stage of embedding -- capacity planning using an LP model
"""
import gurobipy
from gurobipy.gurobipy import quicksum, Model, GRB
import Distance
import vEntities
from layout import Style as style


def linear_program(applications, grouped_users, graph):
    model = Model("placement")
    model.reset()

    # Define variables
    direct, transient = define_variables(model, applications, graph)

    try:
        # Objective function
        model.setObjectiveN(
            quicksum(
                (transient[a, s, i, j, m, n] * graph.edges[(m, n)]['shareCost'] * a.edges[(i, j)]['shareMultiplier'])
                + direct[a, s, i, j, m, n] * (graph.edges[(m, n)]['shareCost'] * a.edges[(i, j)]['shareMultiplier']
                                                   + graph.nodes[n]['shareCost'] * a.nodes[j]['shareMultiplier'])
                for a in applications for i, j in a.edges() for s in graph.nodes() for m in graph.nodes()
                for n in graph.nodes() if (m, n) in graph.edges()
            ), GRB.MINIMIZE)

        # Constraints
        for s in graph.nodes:
            for m in graph.nodes:
                if m != s:
                    if (m, s) in graph.edges:
                        model.addConstr(quicksum(direct[a, s, i, j, m, s] for a in applications
                                                 for i, j in a.edges()) == 0, name="NO FLOW LOOPS")
                        model.addConstr(quicksum(transient[a, s, i, j, m, s] for a in applications
                                                 for i, j in a.edges()) == 0, name="NO FLOW LOOPS")

                    model.addConstr(quicksum(direct[a, s, i, j, m, m] for a in applications
                                             for i, j in a.edges()) == 0, name="NO LOCAL TRANSIENT")
                    model.addConstr(quicksum(transient[a, s, i, j, m, m] for a in applications
                                             for i, j in a.edges()) == 0, name="NO LOCAL TRANSIENT")
                    model.addConstr(quicksum(transient[a, s, i, j, s, s] for a in applications
                                             for i, j in a.edges()) == 0, name="NO LOCAL TRANSIENT")

        for m, n in graph.edges:
            if m != n:
                for s in graph.nodes:
                    for a in applications:
                        for i, j in a.edges():
                            if j == 'T':
                                model.addConstr(direct[a, s, i, j, m, n] == 0, name="LOCAL TERMINATOR")

        for d in graph.nodes:
            for a in applications:
                for i, j in a.edges():
                    for j_, k in a.edges():
                        if j == j_ and a.nodes[j]['isSplitter'] is False:
                            model.addConstr(quicksum(direct[a, s, i, j, m, d] for s in graph.nodes for m in graph.nodes
                                                     if (m, d) in graph.edges()) - quicksum(direct[a, d, j, k, d, n] +
                                                                                            transient[a, d, j, k, d, n]
                                                                                            for n in graph.nodes
                                                                                            if (d, n) in graph.edges()) == 0,
                                            name="DIRECT FLOW PRESERVATION")

        # for d in graph.nodes:  # todo 'consider adding this for spliter scenario'
        #     for a in applications:
        #         for i, j in a.edges():
        #             if a.nodes[j]['isSplitter'] is True:
        #                 model.addConstr(quicksum(direct[a, s, i, j, m, d] for s in graph.nodes for m in graph.nodes
        #                                          if (m, d) in graph.edges()) - quicksum(direct[a, d, j, k, d, n] +
        #                                                                                 transient[a, d, j, k, d, n]
        #                                                                                 for j_, k in a.edges() if j_ == j
        #                                                                                 for n in graph.nodes
        #                                                                                 if (d, n) in graph.edges()) == 0,
        #                                 name="DIRECT FLOW PRESERVATION2")

        for s in graph.nodes:
            for d in graph.nodes:
                if s != d:
                    for a in applications:
                        for i, j in a.edges:
                            model.addConstr(quicksum(transient[a, s, i, j, m, d] for m in graph.nodes if m != d
                                                     if (m, d) in graph.edges) - (quicksum(direct[a, s, i, j, d, n]
                                                                                           + transient[a, s, i, j, d, n]
                                                                                           for n in graph.nodes if n != s
                                                                                           if n != d
                                                                                           if (d, n) in graph.edges)) == 0,
                                            name="TRANSIENT FLOW PRESERVATION")

        for d in graph.nodes:
            for a in applications:
                for u, k in a.edges:
                    if u == 'U':
                        model.addConstr(vEntities.get_aggregate_dc_demand(a, grouped_users, d) -
                                        (quicksum(direct[a, d, u, k, d, n] + transient[a, d, u, k, d, n]
                                                  for n in graph.nodes if (d, n) in graph.edges)) == 0,
                                        name="DEMAND SATISFACTION")

        for d in graph.nodes:
            model.addConstr(quicksum(a.nodes[j]['shareMultiplier'] *
                                     quicksum(direct[a, s, i, j, m, d]
                                              for m in graph.nodes if (m, d) in graph.edges)
                                     for s in graph.nodes for a in applications for i, j in a.edges())
                            <= graph.nodes[d]['shareCap'],
                            name="DATACENTER CAPACITY")

        for m in graph.nodes:
            for n in graph.nodes:
                if (m, n) in graph.edges:
                    model.addConstr(quicksum(a.edges[(i, j)]['shareMultiplier'] *
                                             quicksum(direct[a, s, i, j, m, n] + transient[a, s, i, j, m, n]
                                                      for s in graph.nodes) for a in applications for i, j in a.edges())
                                    <= graph.edges[(m, n)]['shareCap'],
                                    name="LINK CAPACITY")

        for a in applications:
            for i, j in a.edges():
                for s in graph.nodes():
                    for n in graph.nodes:
                        if (s, n) in graph.edges():
                            model.addConstr(direct[a, s, i, j, s, n] * (a.edges[(i, j)]['latencyDemand'] -
                                                                             graph.edges[(s, n)]['latency']) >= 0,
                                            name="SINGLE HOP LATENCY")
                            model.addConstr(transient[a, s, i, j, s, n] * (a.edges[(i, j)]['latencyDemand'] -
                                                                                graph.edges[(s, n)]['latency']) >= 0,
                                            name="SINGLE HOP LATENCY")
        #
        for a in applications:
            for i, j in a.edges():
                for s in graph.nodes():
                    for m, n in graph.edges():
                        if (m != s) and (n != s):
                            # model.addConstr(direct[a, s, i, j, m, n] * Distance.is_monotonic(graph, s, m, n) >= 0,
                            #                 name="MONOTONIC ALLOCATION")
                            # model.addConstr(transient[a, s, i, j, m, n] * Distance.is_monotonic(graph, s, m, n) >= 0,
                            #                 name="MONOTONIC ALLOCATION")

                            model.addConstr(direct[a, s, i, j, m, n] * (a.edges[(i, j)]['latencyDemand'] -
                                                                             Distance.distance(graph, s, n)) >= 0,
                                            name='LATENCY BOUND')

        model.Params.IntFeasTol = 1e-1
        model.optimize()

        if model.Status in (GRB.INF_OR_UNBD, GRB.INFEASIBLE, GRB.UNBOUNDED):
            print(f'{style.RED}Model cannot be solved because it is infeasible or unbounded {style.END}')
            return [model, {('_', '_', '_', '_', '_', '_'): '_'}, {('_', '_', '_', '_', '_', '_'): '_'}]
            # sys.exit(0)

        if model.Status != GRB.OPTIMAL:
            print(f'{style.RED}Optimization was stopped with status {style.END}' + str(model.Status))
            return [model, {('_', '_', '_', '_', '_', '_'): '_'}, {('_', '_', '_', '_', '_', '_'): '_'}]
            # sys.exit(0)

        model.getVars()

    except gurobipy.GurobiError as e:
        print(f'{style.RED}Error code {style.END}' + str(e.errno) + ": " + str(e))

    except AttributeError as e:
        print(f'{style.RED}Encountered an attribute error: {style.END}' + str(e))

    finally:
        # Safely release memory and/or server side resources consumed by the default environment
        gurobipy.disposeDefaultEnv()

    print(f'{style.YELLOW}=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-={style.END}')
    print(f'{style.BOLD}{style.DARKCYAN}Results of the Fluid Model {style.END}')
    print(f'{style.YELLOW}=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-={style.END}')

    print(f'{style.YELLOW}{style.BOLD} ******** First stage of allocations (planning) ******** {style.END}')
    total_cost_direct = 0
    total_cost_direct += print_output('Direct', direct, applications, graph, total_cost_direct)
    total_cost_trans = 0
    total_cost_trans += print_output('Transient', transient, applications, graph, total_cost_trans)

    return [model, direct, transient, total_cost_direct + total_cost_trans]


def define_variables(model, applications, graph):
    """
    Defining variables for the LP model, which are two continuous variables, namely 'direct' and 'transient' variables
    :param model: The original model that we want to define variables for it
    :param applications: list of applications requested by the users
    :param graph: physical network graph
    :return: 'direct' and 'transient' variables
    """
    direct = {}
    transient = {}
    for a in applications:
        for i, j in a.edges:
            for s in graph.nodes:
                for m, n in graph.edges:
                    direct[a, s, i, j, m, n] = model.addVar(vtype=GRB.CONTINUOUS,
                                                                 lb=0, name='Direct [%s, %s, %s, %s, %s, %s]' %
                                                                            (a.name, s, i, j, m, n))

                    transient[a, s, i, j, m, n] = model.addVar(vtype=GRB.CONTINUOUS,
                                                                    lb=0, name='Transient [%s, %s, %s, %s, %s, %s]' %
                                                                               (a.name, s, i, j, m, n))
    return [direct, transient]


def print_output(variable_name, variable, applications, graph, total_cost):
    import network_config as nc
    fictitious = 'dc_edge' + str(nc.number_of_dc_edge + 1)
    total_shares_alloc = 0
    for a in applications:
        for i, j in a.edges():
            for s in graph.nodes:
                for m, n in graph.edges():
                    if variable[a, s, i, j, m, n].X:
                        if s != fictitious and m != fictitious and n != fictitious:
                            if variable_name == 'Direct':
                                total_cost += variable[a, s, i, j, m, n].X * (graph.edges[(m, n)]['shareCost'] *
                                                                                   a.edges[(i, j)]['shareMultiplier'] +
                                                                                   graph.nodes[n]['shareCost'] *
                                                                                   a.nodes[j]['shareMultiplier'])

                            elif variable_name == "Transient":
                                total_cost += variable[a, s, i, j, m, n].X * (graph.edges[(m, n)]['shareCost'] *
                                                                                   a.edges[(i, j)]['shareMultiplier'])

                        value = a.edges[(i, j)]['shareMultiplier'] * variable[a, s, i, j, m, n].X
                        if not value:
                            print(variable_name, ':', a.name, s, i, j, m, n, '----> ',
                                  variable[a, s, i, j, m, n].X, style.BOLD, style.GREEN,
                                  '(No effect on the actual consumed capacity)', style.END)
                        else:
                            print(variable_name, ':', a.name, s, i, j, m, n, '----> ', a.edges[(i, j)]['shareMultiplier']
                                  * variable[a, s, i, j, m, n].X)

                            total_shares_alloc += variable[a, s, i, j, m, n].X

    print(f'{style.PURPLE}{style.UNDERLINE}Total allocated (consumed capacity) shares to the {variable_name} links is: '
          f'{total_shares_alloc}{style.END}')
    return total_cost

