"""
Draw the plots
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import network_config as nc


def get_file_path(variable_name, run_number):
    """
    Returning the exact location to store the performance metrics
    """
    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name
    evaluation_files_path = scenario_path + '/' + 'Run'
    return evaluation_files_path + str(run_number) + '/' + variable_name + '.csv'


def dc_share_utilization(dc_level, graph, datacenters, min_number_of_ue, step_number_of_ue,
                         max_number_of_ue, number_of_runs):
    """
    Plot share utilization on the datacenter of the different levels (edge, transport, and core)
    """
    df_index = 0 if dc_level == 'Edge' else 1 if dc_level == 'Trans' else 2

    variable_name = 'dc_share_utilization'
    datacenters_capacity = 0
    for d in datacenters:
        datacenters_capacity += graph.nodes[d]['shareCap']

    list_of_dfs_of_different_runs = list()
    list_of_dfs_of_different_runs_formatted = list()
    combined_dfs = list()

    for i in range(number_of_runs):
        list_of_dfs_of_different_runs.append(pd.read_csv(get_file_path(variable_name, i + 1),  delimiter=','))
        list_of_dfs_of_different_runs_formatted.append({'numUE': [n for n in range(min_number_of_ue, max_number_of_ue +
                                                                                   min_number_of_ue, step_number_of_ue)],
                                                        'ShareConsumed': [list_of_dfs_of_different_runs[i].iloc[df_index][str(u) + 'UE']
                                                                          * 100 / datacenters_capacity
                                                                          for u in range(min_number_of_ue,
                                                                                         max_number_of_ue +
                                                                                         min_number_of_ue,
                                                                                         step_number_of_ue)]})

        combined_dfs.append(pd.DataFrame(data=list_of_dfs_of_different_runs_formatted[i]))

    # frames stores the concatenated dataframes of all the runs
    frames = [combined_dfs[i] for i in range(number_of_runs)]
    overall_result = pd.concat(frames)

    plt.clf()
    ax = sns.boxplot(x='numUE', y='ShareConsumed', data=overall_result, linewidth=2)
    ax.set_xlabel('Number of users (Load)', fontsize=12)
    ax.set_ylabel(f'ECU utilization at {dc_level} (%)', fontsize=12)

    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name + '/'
    os.makedirs(scenario_path + 'Plots', exist_ok=True)
    plt.savefig(scenario_path + 'Plots/' + dc_level + '_' + variable_name + '.pdf', orientation="landscape", dpi=1200)


def total_dc_share_utilization(graph, min_number_of_ue, step_number_of_ue, max_number_of_ue, number_of_runs):
    """
    Plot total share utilization on all the datacenters (edge, transport, and core)
    """
    variable_name = 'dc_share_utilization'
    list_of_dfs_of_different_runs = list()

    for i in range(number_of_runs):
        list_of_dfs_of_different_runs.append(pd.read_csv(get_file_path(variable_name, i + 1),  delimiter=','))

    number_of_bars_in_x_axis = 10

    share_utilization_edge = [list_of_dfs_of_different_runs[0].loc[0][str(u) + 'UE'] for u in range(min_number_of_ue,
                                                                                                    max_number_of_ue +
                                                                                                    min_number_of_ue,
                                                                                                    step_number_of_ue)]

    share_utilization_trans = [list_of_dfs_of_different_runs[0].loc[1][str(u) + 'UE'] for u in range(min_number_of_ue,
                                                                                                     max_number_of_ue +
                                                                                                     min_number_of_ue,
                                                                                                     step_number_of_ue)]

    share_utilization_core = [list_of_dfs_of_different_runs[0].loc[2][str(u) + 'UE'] for u in range(min_number_of_ue,
                                                                                                    max_number_of_ue +
                                                                                                    min_number_of_ue,
                                                                                                    step_number_of_ue)]

    # index = np.arange(number_of_bars_in_x_axis)
    index = np.arange(len(share_utilization_core))  # can be replaced by the above line in case a different x axis is needed
    width = 0.75  # the width of the bars: it also can be len(x) sequence
    bottom_ = [share_utilization_core[i] + share_utilization_trans[i] for i in range(len(share_utilization_core))]

    plt.clf()
    plot1 = plt.bar(index, share_utilization_core, width, color='#4e89ae')
    plot2 = plt.bar(index, share_utilization_trans, width, color='#94b4a4', bottom=share_utilization_core)
    plot3 = plt.bar(index, share_utilization_edge, width, color='#686d76', bottom=bottom_)

    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)
    plt.grid(color='lightgray', linestyle='--', linewidth=0.3)

    plt.xlabel('Number of Users (Load)', fontsize=12)
    plt.ylabel('Number of ECU utilized', fontsize=12)
    plt.xticks(index, [u for u in range(min_number_of_ue, max_number_of_ue + min_number_of_ue, step_number_of_ue)])

    plt.legend((plot1[0], plot2[0], plot3[0]), ('Core', 'Transport', 'Edge'), loc='upper left', fontsize=12)

    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name + '/'
    os.makedirs(scenario_path + 'Plots', exist_ok=True)
    plt.savefig(scenario_path + 'Plots/' + 'Total' + '_' + variable_name + '.pdf', orientation="landscape", dpi=1200)


def execution_time(graph, min_number_of_ue, step_number_of_ue, max_number_of_ue, number_of_runs):
    """
    Plot average execution of all the runs
    """
    variable_name = 'execution_time'
    list_of_dfs_of_different_runs = list()

    for i in range(number_of_runs):
        list_of_dfs_of_different_runs.append(pd.read_csv(get_file_path(variable_name, i + 1), delimiter=','))

    combined_dfs = pd.concat(list_of_dfs_of_different_runs[i] for i in range(number_of_runs))

    y_axes = [i for i in range(min_number_of_ue, max_number_of_ue, step_number_of_ue)]

    plt.plot(y_axes, combined_dfs.mean().iloc[:step_number_of_ue], marker='s', markerfacecolor='orange',
             markersize=4, color='#1b1015', linewidth=1, label="Small Topology")

    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)
    plt.grid(color='lightgray', linestyle='-', linewidth=0.3)
    plt.xlabel('Number of users (Load)', fontsize=12)
    plt.ylabel('Execution time (sec)', fontsize=12)
    plt.yscale('log')

    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name + '/'
    os.makedirs(scenario_path + 'Plots', exist_ok=True)
    plt.savefig(scenario_path + 'Plots/' + variable_name + '.pdf', orientation="landscape", dpi=1200)


def plot_the_captured_kpis(graph, topology, min_number_of_ue=nc.min_number_of_ue,
                           step_number_of_ue=nc.step_number_of_ue, max_number_of_ue=nc.max_number_of_ue,
                           number_of_runs=nc.number_of_runs):

    # Datacenter Share Utilization
    dc_share_utilization('Edge', graph, topology.dc_edge,
                         min_number_of_ue, step_number_of_ue, max_number_of_ue, number_of_runs)
    dc_share_utilization('Trans', graph, topology.dc_trans,
                         min_number_of_ue, step_number_of_ue, max_number_of_ue, number_of_runs)
    dc_share_utilization('Core', graph, topology.dc_core,
                         min_number_of_ue, step_number_of_ue, max_number_of_ue, number_of_runs)

    total_dc_share_utilization(graph, min_number_of_ue, step_number_of_ue, max_number_of_ue, number_of_runs)

    # execution_time(graph, min_number_of_ue, step_number_of_ue, max_number_of_ue, number_of_runs)


