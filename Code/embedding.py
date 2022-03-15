"""
Embed service into the network
"""

import network_config as nc
import vEntities
from Code import heuristic, plots
from layout import Style as style
import fluid_model
import topology_generator
import evaluations
import math
import numpy as np
import copy

# global lists
edge_dcs_zipf = []
edge_dcs_uniform = []
share_demand_normal = []


def share_demand_with_uniform_distri(number_of_users):
    share_demand_normal.clear()
    mu, sigma = 3, 0.95  # mean and standard deviation
    generated_numbers = abs(np.random.normal(mu, sigma, number_of_users))

    values = (generated_numbers / float(max(generated_numbers))) * 10

    for n in values:
        share_demand_normal.append(math.ceil(n))


def list_of_edge_dc_with_uniform_distri(number_of_users, number_dc_edge):
    edge_dcs_uniform.clear()
    generated_numbers = np.random.uniform(1, number_dc_edge, number_of_users)
    values = (generated_numbers / float(max(generated_numbers))) * number_dc_edge

    for n in values:
        edge_dcs_uniform.append(math.ceil(n))


def list_of_edge_dc_with_zipf_distri(number_of_users, number_dc_edge):
    edge_dcs_zipf.clear()
    generated_numbers = np.random.zipf(2.1, number_of_users)
    values = (generated_numbers / float(max(generated_numbers))) * number_dc_edge

    for n in values:
        edge_dcs_zipf.append(math.ceil(n))


def embed_service():
    """
    building the virtual requests and embed them into the substrate network
    """

    topology = topology_generator.Topology()
    graph, dc_edge = topology.request_handler(nc.topology_source)
    topology.get_info()

    evaluations.create_evaluation_files_and_dir()

    for run_number in range(1, nc.number_of_runs + 1):
        for number_of_users in range(nc.min_number_of_ue, nc.max_number_of_ue + nc.min_number_of_ue,
                                     nc.step_number_of_ue):

            # Generate list of DCs for user association based on a specific distribution
            list_of_edge_dc_with_zipf_distri(number_of_users, nc.number_of_dc_edge)
            list_of_edge_dc_with_uniform_distri(number_of_users, nc.number_of_dc_edge)
            share_demand_with_uniform_distri(number_of_users)

            # get set of all possible applications that can be requested
            apps = vEntities.Application()
            apps.get_info()
            applications_list = apps.get_app_list(nc.number_of_apps)

            # users
            users = add_users(number_of_users, topology.dc_edge)
            vEntities.User.get_info_all_users(users)

            # grouped users (users with same application demand and same edge datacenter association)
            grouped_users = vEntities.User.group_users(users, applications_list)

            # get set of applications that are requested by the users
            applications = add_application(grouped_users, applications_list)

            print_total_share_demand_for_applications(apps, applications, grouped_users)
            print_total_demand_on_the_edge_dcs(topology.dc_edge, apps, applications, grouped_users)

            print(style.YELLOW, '\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=', style.END)

            # call the linear program of the Fluid model to solve the network planning problem (Phase 1)
            model, direct, transient = fluid_model.linear_program(applications, grouped_users, graph)
            evaluate_the_model(topology, model, direct, transient, graph, applications, users, run_number)

            # call the heuristic algorithm to perform per-user allocation based on the inputs from the Fluid model
            num_rejected_users = heuristic.per_user_allocation_heuristic(
                model, direct, transient, applications, copy.deepcopy(graph), users)
            evaluate_the_heuristic(num_rejected_users, users, run_number, 'RejectedUsersFluidModel')

            print('{} DONE for run number {} with {} users {}'
                  .format(style.RED, run_number, number_of_users, style.END))

    plots.plot_the_captured_kpis(graph, topology)


def add_application(grouped_users, applications_list):
    """"
     adding requested application to a set to only loop over them during the placement
    """
    applications = set()
    for g_u in grouped_users:
        for a in applications_list:
            if g_u.app_demand.name == a.name:
                applications.add(a)

    return applications


def add_users(number_of_users, dc_edge):
    """
    adding a set of users
    :param number_of_users: how many users are making request
    :param dc_edge: list of edge datacenters
    :return: return the list of (num_ue) users
    """
    users = set()
    for u in range(1, number_of_users + 1):
        users.add(vEntities.User(u, dc_edge))

    return users


def print_total_share_demand_for_applications(apps, applications, grouped_users):
    """
    print total demand for an application in the entire network
    """
    print('=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
    for a in applications:
        print('Total share demand for application {}{}{} is {} ECU'
              .format(style.BLUE, a.name, style.END, apps.get_aggregate_app_demand(a, grouped_users)))


def print_total_demand_on_the_edge_dcs(dc_edge, apps, applications, grouped_users):
    """
    print total demand for an application on each datacenter
    """
    print('=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
    for d in dc_edge:
        if apps.get_aggregate_dc_demand(applications, grouped_users, d) != 0:
            print('Total share demand for all applications on DC {}{}{} is {} ECU'
                  .format(style.BLUE, d, style.END,
                          apps.get_aggregate_dc_demand(applications, grouped_users, d)))


def evaluate_the_model(topology, model, direct, transient, graph, applications, users, run_number):
    print('Saving the evaluation files...')
    evaluations.save_network_config_file()
    evaluations.dc_share_utilization(topology, model, direct, graph, applications, users, run_number)
    evaluations.link_share_utilization(topology, model, direct, transient, graph, applications, users, run_number)
    evaluations.execution_time(model, users, run_number)


def evaluate_the_heuristic(num_rejected_users, users, run_number, key):
    evaluations.rejected_users(num_rejected_users, users, run_number, key)



