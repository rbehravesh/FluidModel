import pandas as pd
import network_config as nc



def get_file_path(variable_name, run_number):
    """
    Returning the exact location to store the performance metrics
    """
    scenario_path = '../Results/' + nc.evaluation_scenario_name + '/' + nc.topology_name
    evaluation_files_path = scenario_path + '/' + 'Run'
    return evaluation_files_path + str(run_number) + '/' + variable_name + '.csv'


def rejected_users(users_list, rejected_users_list, share_demand_rejected, users_on_fictitious_list,
                   share_demand_on_fictitious, num_users, run_number, total_cost, key):

    file_path = get_file_path('saturation', run_number)
    df = pd.read_csv(file_path, index_col=0)

    num_users_rejected = len(rejected_users_list)
    num_users_on_fictitious = len(users_on_fictitious_list)
    df.loc[key + '_Total_Cost', str(num_users) + 'UE'] = total_cost
    df.loc[key + '_Users', str(num_users) + 'UE'] = num_users_rejected
    df.loc[key + '_Demand', str(num_users) + 'UE'] = share_demand_rejected

    df.loc[key + '_Users_ON_FICTITIOUS', str(num_users) + 'UE'] = num_users_on_fictitious
    df.loc[key + '_Demand_ON_FICTITIOUS', str(num_users) + 'UE'] = share_demand_on_fictitious
    df.loc[key + '_Total_Rejected', str(num_users) + 'UE'] = num_users_rejected + num_users_on_fictitious

    total_app_share_demand = 0
    total_functions_share_demand = 0
    for u in sorted(users_list, key=lambda u: u.id_, reverse=False):
        total_app_share_demand += u.share_demand
        total_functions_share_demand += u.share_demand * (len(u.app_demand.nodes()) - 2)

    df.loc['/////////////////////////////////////////', str(num_users) + 'UE'] = '////////////////'
    df.loc['Total_App_Share_Demand', str(num_users) + 'UE'] = total_app_share_demand
    df.loc['Total_Func_Share_Demand', str(num_users) + 'UE'] = total_functions_share_demand
    df.loc['XXXXXXXXXXXXXXXXXXXXXXXXXXXX', str(num_users) + 'UE'] = 'XXXXXX'
    df.to_csv(file_path, sep=',', encoding='utf-8')


def per_dc_rejection(users_list, dc_edge, rejected_users_list, users_on_fictitious_list, num_users, run_number, key):
    dc_edge_rejected_users = dict((dc, 0) for dc in dc_edge)
    for u in rejected_users_list:
        dc_edge_rejected_users[u.assoc_dc] += 1

    for u in users_on_fictitious_list:
        dc_edge_rejected_users[u.assoc_dc] += 1

    # total_users_on_dc
    total_users = dict((dc, 0) for dc in dc_edge)
    for u in users_list:
        total_users[u.assoc_dc] += 1

    df1 = pd.DataFrame(dc_edge_rejected_users, index=[key + str(num_users)])

    if key == 'SOTA':
        df2 = pd.DataFrame(total_users, index=['total_users_' + str(num_users)])
        df = pd.concat([df1, df2], axis=0)
    else:
        df = df1

    file_path = get_file_path('Per_dc_rejection', run_number)
    import os
    # if file does not exist write header
    if not os.path.isfile(file_path):
        df.to_csv(file_path, header=[dc for dc in dc_edge])
    else:  # else it exists so append without writing the header
        df.to_csv(file_path, mode='a', header=False)


def dc_share_distribution(graph, direct_allocation, num_users, run_number, key):
    a = [[0 for j in range(len(graph.nodes()))] for i in range(len(graph.nodes()))]
    df = pd.DataFrame(a, index=[dc for dc in graph.nodes()], columns=[dc for dc in graph.nodes()])
    for u, a, s, i, j, m, n in direct_allocation:
        if j != 'T':
            df.loc[u.assoc_dc, n] += direct_allocation[u, a, s, i, j, m, n]

    file_path = get_file_path(str(num_users) + key + '_dc_share_distribution', run_number)

    df.to_csv(file_path)


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

    # Saving  results in a file
    df.loc['Sota_Edge', str(num_users) + 'UE'] = edge_share_utilization_sota
    df.loc['Sota_Trans', str(num_users) + 'UE'] = trans_share_utilization_sota
    df.loc['Sota_Core', str(num_users) + 'UE'] = core_share_utilization_sota
    df.to_csv(file_path, sep=',', encoding='utf-8')


def execution_time(num_users, run_number, exec_time, key):
    file_path = get_file_path('execution_time', run_number)
    df = pd.read_csv(file_path, index_col=0)
    df.loc[key + str(nc.topology_name), str(num_users) + 'UE'] = exec_time
    df.to_csv(file_path, sep=',', encoding='utf-8')
