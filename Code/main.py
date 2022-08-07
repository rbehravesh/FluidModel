
import embedding
import network_config as nc
if __name__ == '__main__':
    embedding.embed_service(nc.topology_source, nc.number_of_apps, nc.number_of_runs, nc.min_number_of_ue,
                            nc.max_number_of_ue + nc.min_number_of_ue, nc.step_number_of_ue)
