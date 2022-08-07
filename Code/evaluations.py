import pandas as pd
import network_config as nc
import plots


def get_file_path(variable_name, run_number):
    """
    Returning the exact location to store the performance metrics
    """
    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name
    evaluation_files_path = scenario_path + '/' + 'Run'
    return evaluation_files_path + str(run_number) + '/' + variable_name + '.csv'


def rejected_users(num_rejected_users, share_demand_rejected, users_on_fictitious,
                   share_demand_on_fictitious, num_users, run_number, total_cost, key):

    file_path = get_file_path('saturation', run_number)
    df = pd.read_csv(file_path, index_col=0)

    df.loc[key + '_Total_Cost', str(num_users) + 'UE'] = total_cost
    df.loc[key + '_Users', str(num_users) + 'UE'] = num_rejected_users
    df.loc[key + '_Demand', str(num_users) + 'UE'] = share_demand_rejected

    df.loc[key + '_Users_ON_FICTITIOUS', str(num_users) + 'UE'] = users_on_fictitious
    df.loc[key + '_Demand_ON_FICTITIOUS', str(num_users) + 'UE'] = share_demand_on_fictitious

    import vEntities
    df.loc['/////////////////////////////////////////', str(num_users) + 'UE'] = '////////////////'
    df.loc['Total_Apps_Share_Demand', str(num_users) + 'UE'] = vEntities.User.total_apps_share_demand
    df.loc['Total_Users_Share_Demand', str(num_users) + 'UE'] = vEntities.User.total_users_share_demand
    df.loc['XXXXXXXXXXXXXXXXXXXXXXXXXXXX', str(num_users) + 'UE'] = 'XXXXXX'
    df.to_csv(file_path, sep=',', encoding='utf-8')


def dc_share_utilization(topology, model, direct, num_users, run_number):
    file_path = get_file_path('dc_share_utilization', run_number)
    df = pd.read_csv(file_path, index_col=0)

    edge_share_utilization = 0
    trans_share_utilization = 0
    core_share_utilization = 0

    # Compute share utilization on different datacenters
    for a, s, i, j, m, n in direct:
        if direct[a, s, i, j, m, n].X:
            if n in topology.dc_edge:
                edge_share_utilization += a.nodes[j]['shareMultiplier'] * direct[a, s, i, j, m, n].X
            elif n in topology.dc_trans:
                trans_share_utilization += a.nodes[j]['shareMultiplier'] * direct[a, s, i, j, m, n].X
            elif n in topology.dc_core:
                core_share_utilization += a.nodes[j]['shareMultiplier'] * direct[a, s, i, j, m, n].X

    # Saving the results in a file
    df.loc['Fluid_Edge', str(num_users) + 'UE'] = edge_share_utilization
    df.loc['Fluid_Trans', str(num_users) + 'UE'] = trans_share_utilization
    df.loc['Fluid_Core', str(num_users) + 'UE'] = core_share_utilization
    df.to_csv(file_path, sep=',', encoding='utf-8')


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
        shutil.copy('../Results/Template/saturation.csv', evaluation_files_path)

##########################################################################################
# SOTA
##########################################################################################
def dc_share_utilization_sota(topology, edge_share_utilization_sota, trans_share_utilization_sota,
                                              core_share_utilization_sota, num_users, run_number):
    file_path = get_file_path('dc_share_utilization', run_number)
    df = pd.read_csv(file_path, index_col=0)

    # Saving the results in a file
    df.loc['Sota_Edge', str(num_users) + 'UE'] = edge_share_utilization_sota
    df.loc['Sota_Trans', str(num_users) + 'UE'] = trans_share_utilization_sota
    df.loc['Sota_Core', str(num_users) + 'UE'] = core_share_utilization_sota
    df.to_csv(file_path, sep=',', encoding='utf-8')


def execution_time(num_users, run_number, exec_time, key):
    file_path = get_file_path('execution_time', run_number)
    df = pd.read_csv(file_path, index_col=0)
    df.loc[key + str(nc.topology_name), str(num_users) + 'UE'] = exec_time
    df.to_csv(file_path, sep=',', encoding='utf-8')
