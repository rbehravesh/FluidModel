"""
Configure the input parameters of the network.
The input parameters include
 - user parameters
 - simulation time parameters
 - number of applications and functions
 - topology size
"""

path_to_the_topology = '../FixedTopologies/'  # for loading or storing topologies
topology_source = 'load'  # select from 'load' and 'generate
evaluation_scenario_name = 'StrictWithMultiplier'

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
topology_name = 'NEWTOPOLOGY'  # 'small' - 'medium' - 'big' #NEWTOPOLOGY

min_number_of_ue = 10
max_number_of_ue = 100
step_number_of_ue = 10

number_of_runs = 5

number_of_functions = 6  # max 6
number_of_apps = 2  # max 5

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""
Generate a topology from the given configurations
 - it will be used only if a different topology from the already existing ones is needed
 - each DC (edge, transport, and core) has its own set of computing shares (elastic capacity units (ECU))
 - each DC (edge, transport, and core) has a defined cost for each ECU
 - each link (xn, fh, bh, tr, inDC) has its own set of communication shares (elastic capacity units (ECU))
 - each link (xn, fh, bh, tr, inDC) has a defined cost for each ECU
"""

# computing nodes
k = 10**3
number_of_dc_edge = 200  # 40 # 100
number_of_dc_trans = 10
number_of_dc_core = 3

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

link_share_cost_xn = 0
link_share_cost_fh = 0
link_share_cost_bh = 0
link_share_cost_tr = 0
link_share_cost_inDC = 0
