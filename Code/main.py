
import sfc_placement
import network_config as nc
if __name__ == '__main__':
    sfc_simulation = sfc_placement.NetworkSimulation(nc.number_of_apps, nc.number_of_runs, nc.min_number_of_ue,
                                                     nc.max_number_of_ue, nc.step_number_of_ue)
    sfc_simulation.run_simulation()
