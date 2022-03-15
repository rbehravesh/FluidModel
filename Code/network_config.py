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
evaluation_scenario_name = 'PerformanceSaturation'

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
topology_name = 'medium'  # 'small' - 'medium' - 'big'

min_number_of_ue = 100
max_number_of_ue = 1000
step_number_of_ue = 100

number_of_runs = 1

number_of_functions = 6  # max 6
number_of_apps = 1  # max 5

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
number_of_dc_edge = 40
number_of_dc_trans = 15
number_of_dc_core = 30

dc_share_cap_edge = 200
dc_share_cap_trans = 400
dc_share_cap_core = 2500

dc_share_cost_edge = 50  # in $
dc_share_cost_trans = 10
dc_share_cost_core = 1

# links
link_share_cap_xn = 200
link_share_cap_fh = 600
link_share_cap_bh = 7500
link_share_cap_tr = 1200
link_share_cap_inDC = 999999999  # link capacity inside DCs

link_share_cost_xn = 0.5
link_share_cost_fh = 0.2
link_share_cost_bh = 0.1
link_share_cost_tr = 0.1
link_share_cost_inDC = 0.01

