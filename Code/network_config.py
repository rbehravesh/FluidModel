"""
Configure the input parameters of the network.
The input parameters include
 - user parameters
 - simulation time parameters
 - number of applications and functions
 - topology size
"""

path_to_the_topology = '../FixedTopologies/'  # for loading or storing topologies
evaluation_scenario_name = 'Test' #RelaxedLatencyXZipfLoadXUniformAppShareX2Apps

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# list_of_topologies = ['10N20E', '20N30E', '40N60E', '50N50E', '60N90E', '80N120E', '100N150E', 'citta_studi',
#                           '5GEN']
list_of_topologies = ['10N20E']

topology_name = '10N20E'
k = 10**3
m = 10**6

min_number_of_ue = 2
max_number_of_ue = 2
step_number_of_ue = 2

number_of_runs = 1

number_of_functions = 6  # max 6
number_of_apps = 1  # max 5

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# computing nodes
num_nodes_dic = {
    '5GEN': [78, 4, 2],
    '10N20E': [8, 0, 2],
    '20N30E': [17, 0, 3],
    '40N60E': [37, 0, 3],
    '50N50E': [47, 0, 3],
    '60N90E': [57, 0, 3],
    '80N120E': [77, 0, 3],
    '100N150E': [97, 0, 3],
    'citta_studi': [24, 0, 6]
}

number_of_dc_edge = num_nodes_dic[topology_name][0]
number_of_dc_trans = num_nodes_dic[topology_name][1]
number_of_dc_core = num_nodes_dic[topology_name][2]

dc_share_cap_edge = 10 * k
dc_share_cap_trans = 200 * k
dc_share_cap_core = 2500 * k

dc_share_cost_edge = 50  # in $
dc_share_cost_trans = 10
dc_share_cost_core = 1

# links
link_share_cap_xn = 10 * k
link_share_cap_fh = 20 * k
link_share_cap_bh = 200 * k
link_share_cap_tr = 100 * k
link_share_cap_inDC = 999999999  # link capacity inside DCs

# link_share_cost_xn = 0.5
# link_share_cost_fh = 0.2
# link_share_cost_bh = 0.1
# link_share_cost_tr = 0.1
# link_share_cost_inDC = 0.01

link_share_cost_xn = 0.1
link_share_cost_fh = 0.2
link_share_cost_bh = 0.2
link_share_cost_tr = 0.2
link_share_cost_inDC = 0.001

