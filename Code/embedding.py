"""
Embed service into the network
"""
import random
import timeit
import vEntities
from Code import heuristic, sota
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
share_demand_uniform = []


def share_demand_with_uniform_distri(number_of_users):
    share_demand_uniform.clear()
    mu, sigma = 3, 0.95  # mean and standard deviation
    generated_numbers = abs(np.random.normal(mu, sigma, number_of_users))

    values = (generated_numbers / float(max(generated_numbers))) * 9

    for n in values:
        share_demand_uniform.append(math.ceil(n))


def list_of_edge_dc_with_uniform_distri(number_of_users, number_dc_edge):
    edge_dcs_uniform.clear()
    generated_numbers = np.random.uniform(1, number_dc_edge, number_of_users)
    values = (generated_numbers / float(max(generated_numbers))) * number_dc_edge

    for n in values:
        edge_dcs_uniform.append(math.ceil(n))


def list_of_edge_dc_with_zipf_distri2(number_of_users, number_dc_edge):
    edge_dcs_zipf.clear()
    generated_numbers = np.random.zipf(2.1, number_of_users)
    values = (generated_numbers / float(max(generated_numbers))) * number_dc_edge

    for n in values:
        edge_dcs_zipf.append(math.ceil(n))


def list_of_edge_dc_with_zipf_distri(number_of_users, number_dc_edge):
    edge_dcs_zipf.clear()
    generated_numbers = np.random.zipf(2.1, number_of_users)
    values = (generated_numbers / float(max(generated_numbers))) * number_dc_edge

    for n in values:
        edge_dcs_zipf.append(math.ceil(n))


def embed_service(topology_source, number_of_apps, number_of_runs, min_number_of_ue, max_number_of_ue,
                  step_number_of_ue):
    """
    building virtual requests and embed them into the substrate network
    """
    topology = topology_generator.Topology()
    graph, dc_edge = topology.request_handler(topology_source)
    topology.get_info()

    evaluations.create_evaluation_files_and_dir()

    for run_number in range(1, number_of_runs + 1):
        for number_of_users in range(min_number_of_ue, max_number_of_ue, step_number_of_ue):

            # Generate list of DCs for user association based on a specific distribution
            list_of_edge_dc_with_zipf_distri(number_of_users, len(dc_edge))
            list_of_edge_dc_with_uniform_distri(number_of_users, len(dc_edge))
            share_demand_with_uniform_distri(number_of_users)

            # List of all possible applications
            applications_list = [vEntities.Application(app_id=i + 1) for i in range(number_of_apps)]

            # List of users todo: change  based on the scenario
            users_list = [vEntities.User(id_=u, app_demand=random.choice(applications_list),
                                         share_demand=share_demand_uniform[u], edge_assoc=edge_dcs_uniform[u])
                          for u in range(number_of_users)]

            vEntities.print_users_information(users_list)

            # Aggregate demand -- users with same application demand and same edge datacenter association
            grouped_users = vEntities.User.group_users(users_list, applications_list, dc_edge)

            # List of applications that are requested by the users
            applications = list({g_u.app_demand for g_u in grouped_users})

            print(style.YELLOW, '\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=', style.END)

            # ======================================================
            # Create a fictitious DC to support all the demand
            fictitious_dcs = ['fic']
            graph.add_nodes_from(
                fictitious_dcs, lat=None, lon=None, color='black', shareCap=10 ** 20,
                shareCost=1000, label='Edge Nodes')

            for n in dc_edge:
                graph.add_edge(n, fictitious_dcs[0], distance=1, shareCap=10 ** 20, shareCost=0.001, latency=0)
                graph.add_edge(fictitious_dcs[0], fictitious_dcs[0], distance=0, shareCap=10 ** 20, shareCost=0,
                               latency=0)
            # ======================================================

            # Fluid model
            model, direct, transient, total_cost_fluid = fluid_model.linear_program(applications, grouped_users, graph)
            evaluate_fluid_model(topology, model, direct, number_of_users, run_number)

            # Heuristic algorithm to perform per-user allocation based on the inputs from the Fluid model
            num_rejected_users, share_amount_rejected, users_on_fictitious, share_amount_on_fictitious, exec_time_heu = \
                heuristic.per_user_allocation_heuristic(model, direct, transient, copy.deepcopy(graph),
                                                        users_list, fictitious_dcs)

            evaluate_heuristic(num_rejected_users, share_amount_rejected, users_on_fictitious,
                               share_amount_on_fictitious, number_of_users, run_number, total_cost_fluid, exec_time_heu,
                               'DeniedFluid')

            # SOTA
            num_rejected_users_sota, share_amount_rejected_sota, users_on_fictitious_sota, \
            share_amount_on_fictitious_sota, exec_time_sota, total_cost_sota, \
            edge_share_utilization_sota, trans_share_utilization_sota, core_share_utilization_sota \
                = sota.service_embedding(users_list, copy.deepcopy(graph), fictitious_dcs)

            evaluate_sota(topology, number_of_users,
                          run_number, num_rejected_users_sota, share_amount_rejected_sota, users_on_fictitious_sota,
                          share_amount_on_fictitious_sota, exec_time_sota, total_cost_sota, edge_share_utilization_sota,
                          trans_share_utilization_sota, core_share_utilization_sota, 'DeniedSOTA')

            print('{} DONE for run number {} with {} users {}'
                  .format(style.RED, run_number, number_of_users, style.END))


def evaluate_fluid_model(topology, model, direct, num_users, run_number):
    print('Saving evaluation files...')
    evaluations.dc_share_utilization(topology, model, direct, num_users, run_number)
    evaluations.execution_time(num_users, run_number, model.Runtime, 'Fluid_')


def evaluate_heuristic(num_rejected_users, share_demand_rejected, users_on_fictitious, share_demand_on_fictitious,
                       num_users, run_number, total_cost_fluid, exec_time_heu, key):
    evaluations.rejected_users(num_rejected_users, share_demand_rejected, users_on_fictitious,
                               share_demand_on_fictitious, num_users, run_number, total_cost_fluid, key)

    evaluations.execution_time(num_users, run_number, exec_time_heu, 'Heu_')


def evaluate_sota(topology, num_users, run_number, num_rejected_users,
                  share_demand_rejected, users_on_fictitious, share_demand_on_fictitious, exec_time_sota,
                  total_cost_sota,
                  edge_share_utilization_sota, trans_share_utilization_sota, core_share_utilization_sota, key):
    print('Saving the SOTA evaluation files...')
    evaluations.rejected_users(num_rejected_users, share_demand_rejected, users_on_fictitious,
                               share_demand_on_fictitious, num_users, run_number, total_cost_sota, key)
    evaluations.dc_share_utilization_sota(topology, edge_share_utilization_sota, trans_share_utilization_sota,
                                          core_share_utilization_sota, num_users, run_number)

    evaluations.execution_time(num_users, run_number, exec_time_sota, 'Sota_')
