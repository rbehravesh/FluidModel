# A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks

## Overview

This repository contains the code and supplementary materials for the paper titled "A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks" by Rasoul Behravesh, David Breitgand, Dean H. Lorenz, and Danny Raz. The paper addresses the efficient deployment of Service Function Chains (SFCs) across edge-to-cloud networks, a problem known to be NP-hard. The authors propose a novel near-optimal heuristic that is both efficient and scalable, outperforming existing state-of-the-art solutions.

The paper was [published in IEEE INFOCOM 2024](https://doi.org/10.1109/INFOCOM52122.2024.10621162), Vancouver, BC, Canada, 2024. It is also available on [arXiv:2401.07611](https://doi.org/10.48550/arXiv.2401.07611).

## Getting Started

### Prerequisites

Ensure you have the following dependencies installed:
- Python 3.x
- Required libraries: Gurobi, Networkx

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/SFC-Deployment-Edge-to-Cloud.git
    cd SFC-Deployment-Edge-to-Cloud
    ```

2. Install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

To run the heuristic algorithm and compare it with the baseline solutions, follow these steps:

1. Navigate to the `code/` directory:
    ```bash
    cd code
    ```

2. Run the main script with the desired parameters:
    ```bash
    python main.py --topology ../data/topology.json --requests ../data/requests.json --output ../results/output.json
    ```

### Evaluation

The evaluation results provided in the paper are based on realistic network topologies and large-scale request scenarios. The `results/` directory contains sample output files that demonstrate the performance of the proposed heuristic.

## Contributing

We welcome contributions to this project. If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## Authors

- Rasoul Behravesh
- David Breitgand
- Dean H. Lorenz
- Danny Raz

## Citation

If you use this code in your research, please cite the paper:

```
@INPROCEEDINGS{behravesh2024sfc,
  author={Behravesh, Rasoul and Breitgand, David and Lorenz, Dean H. and Raz, Danny},
  booktitle={IEEE INFOCOM 2024 - IEEE Conference on Computer Communications}, 
  title={A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks}, 
  year={2024},
  volume={},
  number={},
  pages={751-760},
  keywords={Cloud computing;Multi-access edge computing;Service function chaining;Network topology;Topology;NFV;VNE;SFC;5G/6G;Edge Computing},
  doi={10.1109/INFOCOM52122.2024.10621162}}
```

## Reference

For more details, please refer to our paper: <br>
R. Behravesh, D. Breitgand, D. H. Lorenz and D. Raz, "[A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks](https://doi.org/10.1109/INFOCOM52122.2024.10621162)," IEEE INFOCOM 2024 - IEEE Conference on Computer Communications, Vancouver, BC, Canada, 2024, pp. 751-760, [arXiv:2401.07611](https://doi.org/10.48550/arXiv.2401.07611).
