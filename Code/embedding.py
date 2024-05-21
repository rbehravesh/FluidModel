"""
Embed service into the network
"""

# Standard library imports
import copy
import math
import os
import random
import timeit

# Third-party library imports
import numpy as np
import pandas as pd

# Local application/library specific imports
import evaluations  # Module for handling evaluations
import fluid_model  # Module for the fluid model logic
import network_config as nc  # Configuration for network settings
import topology_generator  # Module for generating network topologies
import vEntities  # Module for virtual entities (like users, applications, etc.)

from Code import heuristic, sota  # Import heuristic and state-of-the-art algorithms
from layout import Style as style  # Import style settings for layout

# Global lists used across the module
edge_dcs_zipf = []  # List to store edge data centers using Zipf distribution
edge_dcs_uniform = []  # List to store edge data centers using uniform distribution
share_demand_normal = []  # List to store shared demand following a normal distribution


def share_demand_with_normal_distri(number_of_users):
    """
        Generate share demand for a given number of users based on a normal distribution.

        This function populates the global list 'share_demand_normal' with demand values. Each value is
        scaled and rounded up to the nearest integer. The demand values are generated such that they
        are proportional to a normal distribution and scaled between 0 and 90.
    """

    # Clearing existing values in the global list
    share_demand_normal.clear()

    # Parameters for the normal distribution: mean (mu) and standard deviation (sigma)
    mu, sigma = 3, 0.95

    # Generate absolute values from a normal distribution
    generated_numbers = abs(np.random.normal(mu, sigma, number_of_users))

    # Scale the numbers to a maximum of 90 and round up to the nearest integer
    scaled_values = (generated_numbers / float(max(generated_numbers))) * 90
    share_demand_normal.extend(math.ceil(n) for n in scaled_values)


def list_of_edge_dc_with_uniform_distri(dc_edge, number_of_users):
    """
        Generate a list of edge data centers (DCs) using a uniform distribution.

        This function selects edge DCs uniformly from a given list and returns their numeric identifiers.
        The 'dc_edge' string identifiers are converted to integers for further processing.
    """
    # Uniformly select edge DCs from the list
    selected_edges = np.random.choice(dc_edge, number_of_users)

    # Extract and return the numeric part of each selected edge DC identifier
    return [int(n.lstrip('dc_edge')) for n in selected_edges]


def list_of_edge_dc_with_zipf_distri(topo_name, dc_edge, number_of_users=None, shuffle=True):
    """
        Generate a list of edge data centers using Zipf distribution.
        """

    alpha = 1.2
    sample_range = np.arange(1, len(dc_edge) + 1)
    probabilities = 1.0 / np.power(sample_range, alpha)
    probabilities /= np.sum(probabilities)

    dc_edges_priority_map = {
        '10N20E': ['dc_edge2', 'dc_edge10', 'dc_edge8', 'dc_edge6', 'dc_edge1'],
        '20N30E': ['dc_edge5', 'dc_edge19', 'dc_edge9', 'dc_edge6', 'dc_edge20'],
        '40N60E': ['dc_edge12', 'dc_edge35', 'dc_edge9', 'dc_edge2', 'dc_edge24'],
        '50N50E': ['dc_edge43', 'dc_edge33', 'dc_edge34', 'dc_edge24', 'dc_edge22'],
        '60N90E': ['dc_edge23', 'dc_edge52', 'dc_edge53', 'dc_edge22', 'dc_edge60'],
        '80N120E': ['dc_edge45', 'dc_edge22', 'dc_edge21', 'dc_edge8', 'dc_edge32'],
        '100N150E': ['dc_edge64', 'dc_edge65', 'dc_edge51', 'dc_edge82', 'dc_edge47'],
        'citta_studi': ['dc_edge14', 'dc_edge9', 'dc_edge21', 'dc_edge7', 'dc_edge29'],
        '5GEN': ['dc_edge25', 'dc_edge41', 'dc_edge15', 'dc_edge27', 'dc_edge71']
    }

    dc_edges_pri = dc_edges_priority_map.get(topo_name, [])
    # Reorder probabilities based on priority of edge DCs
    for dc in dc_edges_pri:
        if dc in dc_edge:
            dc_edge_index = dc_edge.index(dc)
            prob_index = np.argmax(probabilities)
            probabilities[dc_edge_index], probabilities[prob_index] = probabilities[prob_index], probabilities[
                dc_edge_index]

    samples = np.random.choice(dc_edge, size=number_of_users, replace=True, p=probabilities)
    return [int(n.replace('dc_edge', '')) for n in samples]


def embed_service(number_of_apps, number_of_runs, min_number_of_ue, max_number_of_ue,
                  step_number_of_ue):
    """
    building virtual requests and embed them into the substrate network
    """
    for topology_id in nc.list_of_topologies:
        # Initialize and load topology
        topology = topology_generator.Topology(topology_id)
        graph, dc_edge = topology.load_topology(nc.path_to_the_topology)
        topology.get_info()

        # Create necessary directories and files for evaluation
        evaluations.create_evaluation_files_and_dir()

        # Construct the path for users profile to sore info for different runs
        for run_number in range(1, number_of_runs + 1):
            user_profile_address = "../Results/" + nc.evaluation_scenario_name + "/" + \
                                   topology_id + "/Run" + str(run_number) + "/usersProfile.txt"
            try:
                os.remove(user_profile_address)
            except OSError:
                pass

            # Generate list of Data Centers (DCs) for user association based on a Zipf distribution
            edge_dcs_zipf = list_of_edge_dc_with_zipf_distri(topology_id, list(dc_edge), max_number_of_ue)

            # Generate list of DCs for user association based on a uniform distribution
            edge_dcs_uniform = list_of_edge_dc_with_uniform_distri(list(dc_edge), max_number_of_ue)

            # Generate share demand for users based on a normal distribution
            share_demand_with_normal_distri(max_number_of_ue)

            # Create a list of Application instances, one for each application
            applications_list = [vEntities.Application(app_id=i + 1) for i in range(number_of_apps)]

            users_list = [vEntities.User(id_=u, app_demand=random.choice(applications_list),
                                         share_demand=share_demand_normal[u], edge_assoc=edge_dcs_zipf[u])
                          for u in range(max_number_of_ue)]

            # Open the user profile file and write user data
            with open(user_profile_address, "w") as outfile:
                for user in users_list:
                    # Construct a comma-separated string of user attributes
                    user_data = f"{user.id_},{user.app_demand.name},{user.assoc_dc},{user.share_demand}\n"
                    outfile.write(user_data)

            for number_of_users in range(min_number_of_ue, max_number_of_ue + min_number_of_ue, step_number_of_ue):
                users_list = []
                with open(user_profile_address) as input_file:
                    lines = [next(input_file).replace('\n', '') for _ in range(number_of_users)]

                for line in lines:
                    u, app, assoc_dc, share_demand = line.split(',')
                    for a in applications_list:
                        if a.graph.name == app:
                            app = a
                    users_list.append(vEntities.User(id_=int(u[1:]) - 1, app_demand=app,
                                                     share_demand=int(share_demand), edge_assoc=assoc_dc[7:]))
                #
                # users_list = [vEntities.User(id_=u, app_demand=random.choice(applications_list),
                #                              share_demand=share_demand_uniform[u], edge_assoc=edge_dcs_zipf[u])
                #               for u in range(number_of_users)]

                # vEntities.print_users_information(users_list)

                # Aggregate demand -- users with same application demand and same edge datacenter association
                grouped_users = vEntities.User.group_users(users_list, applications_list, dc_edge)

                # List of applications that are requested by the users
                applications = set([vEntities.Application(g_u.app_demand) for g_u in grouped_users])

                print(style.YELLOW, '\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=',
                      style.END)

                # ======================================================
                # Create a fictitious DC to support all     the demand
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
                model, direct, transient, total_cost_fluid = fluid_model.linear_program(applications, grouped_users,
                                                                                        graph)
                evaluate_fluid_model(topology, model, direct, number_of_users, run_number)

                # Heuristic algorithm to perform per-user allocation based on the inputs from the Fluid model
                direct_allocation_fluid, transient_allocation_fluid, rejected_users, share_amount_rejected, \
                users_on_fictitious, share_amount_on_fictitious, \
                exec_time_heu = \
                    heuristic.per_user_allocation_heuristic(model, direct, transient, copy.deepcopy(graph),
                                                            users_list, fictitious_dcs)

                # evaluate_heuristic(graph, direct_allocation_fluid, transient_allocation_fluid, users_list, rejected_users,
                #                    share_amount_rejected, users_on_fictitious, share_amount_on_fictitious,
                #                    number_of_users, run_number, total_cost_fluid, exec_time_heu,dc_edge, 'DeniedFluid')

                # SOTA
                # rejected_users_sota, share_amount_rejected_sota, users_on_fictitious_sota, \
                # share_amount_on_fictitious_sota, exec_time_sota, total_cost_sota, \
                # edge_share_utilization_sota, trans_share_utilization_sota, core_share_utilization_sota \
                #     = sota.service_embedding(users_list, graph.copy(), fictitious_dcs, run_number)

                # evaluate_sota(dc_edge, users_list, topology, number_of_users,
                #               run_number, rejected_users_sota, share_amount_rejected_sota, users_on_fictitious_sota,
                #               share_amount_on_fictitious_sota, exec_time_sota, total_cost_sota, edge_share_utilization_sota,
                #               trans_share_utilization_sota, core_share_utilization_sota, 'DeniedSOTA')

                print('{} DONE for topo {} run number {} with {} users {}'
                      .format(style.RED, topology_id, run_number, number_of_users, style.END))


def evaluate_fluid_model(topology, model, direct, num_users, run_number):
    print('Saving evaluation files...')
    evaluations.dc_share_utilization(topology, model, direct, num_users, run_number)
    evaluations.execution_time(num_users, run_number, model.Runtime, 'Fluid_')


def evaluate_heuristic(graph, direct_allocation, transient_allocation, users_list, rejected_users,
                       share_demand_rejected, users_on_fictitious, share_demand_on_fictitious,
                       num_users, run_number, total_cost_fluid, exec_time_heu, dc_edge, key):
    evaluations.dc_share_distribution(graph, direct_allocation, num_users, run_number, 'FLUID')

    evaluations.per_dc_rejection(users_list, dc_edge, rejected_users, users_on_fictitious, num_users, run_number,
                                 'Fluid')

    evaluations.rejected_users(users_list, rejected_users, share_demand_rejected, users_on_fictitious,
                               share_demand_on_fictitious, num_users, run_number, total_cost_fluid, key)

    evaluations.execution_time(num_users, run_number, exec_time_heu, 'Heu_')


def evaluate_sota(dc_edge, users_list, topology, num_users, run_number, rejected_users,
                  share_demand_rejected, users_on_fictitious, share_demand_on_fictitious, exec_time_sota,
                  total_cost_sota,
                  edge_share_utilization_sota, trans_share_utilization_sota, core_share_utilization_sota, key):
    print('Saving the SOTA evaluation files...')

    # evaluations.dc_share_distribution(graph, direct_allocation, num_users, run_number, 'SOTA')

    evaluations.per_dc_rejection(users_list, dc_edge, rejected_users, users_on_fictitious, num_users, run_number,
                                 'SOTA')

    evaluations.rejected_users(users_list, rejected_users, share_demand_rejected, users_on_fictitious,
                               share_demand_on_fictitious, num_users, run_number, total_cost_sota, key)
    evaluations.dc_share_utilization_sota(topology, edge_share_utilization_sota, trans_share_utilization_sota,
                                          core_share_utilization_sota, num_users, run_number)

    evaluations.execution_time(num_users, run_number, exec_time_sota, 'Sota_')


def save_per_user_allocation(user_alloc_file, direct_allocation, transient_allocation):
    import csv, pandas, pickle, json
    with open(user_alloc_file, 'w') as f:
        f.write(str(direct_allocation))
