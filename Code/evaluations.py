import pandas as pd
from vEntities import Function, Link
import network_config as nc
import plots


def get_file_path(variable_name, run_number):
    """
    Returning the exact location to store the performance metrics
    """
    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name
    evaluation_files_path = scenario_path + '/' + 'Run'
    return evaluation_files_path + str(run_number) + '/' + variable_name + '.csv'


def rejected_users(num_rejected_users, users, run_number, key):
    file_path = get_file_path('saturation', run_number)
    df = pd.read_csv(file_path, index_col=0)

    df.loc[key, str(len(users)) + 'UE'] = num_rejected_users

    df.to_csv(file_path, sep=',', encoding='utf-8')


def dc_share_utilization(topology, model, direct, graph, applications, users, run_number):
    file_path = get_file_path('dc_share_utilization', run_number)
    df = pd.read_csv(file_path, index_col=0)

    edge_share_utilization = 0
    trans_share_utilization = 0
    core_share_utilization = 0

    # Compute share utilization on different datacenters
    for a in applications:
        for i, j in a.edges():
            for s in graph.nodes():
                for m, n in graph.edges():
                    if direct[a.name, s, i, j, m, n].X:
                        if n in topology.dc_edge:
                            edge_share_utilization += Function(j).get_share_multiplier(n) * a.nodes[j]['shareDemand'] \
                                                      * direct[a.name, s, i, j, m, n].X
                        elif n in topology.dc_trans:
                            trans_share_utilization += Function(j).get_share_multiplier(n) * a.nodes[j]['shareDemand'] \
                                                       * direct[a.name, s, i, j, m, n].X
                        else:
                            core_share_utilization += Function(j).get_share_multiplier(n) * a.nodes[j]['shareDemand'] \
                                                      * direct[a.name, s, i, j, m, n].X

    # Saving the results in a file
    df.loc['Fluid_Edge', str(len(users)) + 'UE'] = edge_share_utilization
    df.loc['Fluid_Trans', str(len(users)) + 'UE'] = trans_share_utilization
    df.loc['Fluid_Core', str(len(users)) + 'UE'] = core_share_utilization
    df.to_csv(file_path, sep=',', encoding='utf-8')


def link_share_utilization(topology, model, direct, transient, graph, applications, users, run_number):
    file_path = get_file_path('link_share_utilization', run_number)
    df = pd.read_csv(file_path, index_col=0)

    xn_share_utilization = 0
    fh_share_utilization = 0
    tr_share_utilization = 0
    bh_share_utilization = 0

    for s in graph.nodes():
        for a in applications:
            for i, j in a.edges():
                for m, n in graph.edges():
                    if (m, n) in topology.e_xn:
                        xn_share_utilization += Link(i, j).get_share_multiplier((m, n)) * a.edges[(i, j)]['shareDemand'] \
                                                * (direct[a.name, s, i, j, m, n].X + transient[a.name, s, i, j, m, n].X)
                    elif (m, n) in topology.e_fh:
                        fh_share_utilization += Link(i, j).get_share_multiplier((m, n)) * a.edges[(i, j)]['shareDemand'] \
                                                * (direct[a.name, s, i, j, m, n].X + transient[a.name, s, i, j, m, n].X)
                    elif (m, n) in topology.e_bh:
                        bh_share_utilization += Link(i, j).get_share_multiplier((m, n)) * a.edges[(i, j)]['shareDemand'] \
                                                * (direct[a.name, s, i, j, m, n].X + transient[a.name, s, i, j, m, n].X)
                    elif (m, n) in topology.e_trans:
                        tr_share_utilization += Link(i, j).get_share_multiplier((m, n)) * a.edges[(i, j)]['shareDemand'] \
                                                * (direct[a.name, s, i, j, m, n].X + transient[a.name, s, i, j, m, n].X)

    # Saving the results
    df.loc['Fluid_XN', str(len(users)) + 'UE'] = xn_share_utilization
    df.loc['Fluid_FH', str(len(users)) + 'UE'] = fh_share_utilization
    df.loc['Fluid_Intra_TR', str(len(users)) + 'UE'] = tr_share_utilization
    df.loc['Fluid_BH', str(len(users)) + 'UE'] = bh_share_utilization
    df.to_csv(file_path, sep=',', encoding='utf-8')


def execution_time(model, users, run_number):
    file_path = get_file_path('execution_time', run_number)
    df = pd.read_csv(file_path, index_col=0)
    df.loc['Fluid_' + str(nc.topology_name), str(len(users)) + 'UE'] = model.Runtime
    df.to_csv(file_path, sep=',', encoding='utf-8')


def save_network_config_file():
    with open('network_config.py', 'r') as firstfile, open('../Results/' + nc.evaluation_scenario_name + '/' +
                                                           nc.topology_name + '/    network_configurations.txt',
                                                           'w') as secondfile:
        for line in firstfile:
            secondfile.write(line)


def create_evaluation_files_and_dir():
    import os
    import shutil

    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name
    os.makedirs(scenario_path, exist_ok=True)

    for i in range(1, nc.number_of_runs + 1):
        evaluation_files_path = scenario_path + '/' + 'Run' + str(i)
        os.makedirs(evaluation_files_path, exist_ok=True)
        shutil.copy('../Results/Template/execution_time.csv', evaluation_files_path)
        shutil.copy('../Results/Template/dc_share_utilization.csv', evaluation_files_path)
        shutil.copy('../Results/Template/link_share_utilization.csv', evaluation_files_path)
        shutil.copy('../Results/Template/saturation.csv', evaluation_files_path)
