# A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks

## Overview

This repository contains the code and supplementary materials for the paper titled "A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks" by Rasoul Behravesh, David Breitgand, Dean H. Lorenz, and Danny Raz. The paper addresses the efficient deployment of Service Function Chains (SFCs) across edge-to-cloud networks, a problem known to be NP-hard. The authors propose a novel near-optimal heuristic that is both efficient and scalable, outperforming existing state-of-the-art solutions.

The paper was accepted to IEEE INFOCOM 2024 and is available on arXiv: [arXiv:2401.07611](https://doi.org/10.48550/arXiv.2401.07611).

## Contents

- `code/`: Contains the implementation of the proposed heuristic and the baseline algorithms used for comparison.
- `data/`: Includes the realistic topologies and datasets used in the evaluations.
- `results/`: Contains the results of the large-scale evaluations.
- `docs/`: Additional documentation and resources.

## Getting Started

### Prerequisites

Ensure you have the following dependencies installed:
- Python 3.x
- Required Python libraries (listed in `requirements.txt`)

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

If you use this code or dataset in your research, please cite the paper:

```
@article{behravesh2024sfc,
  title={A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks},
  author={Behravesh, Rasoul and Breitgand, David and Lorenz, Dean H. and Raz, Danny},
  journal={arXiv preprint arXiv:2401.07611},
  year={2024}
}
```

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgments

We thank the researchers and developers who provided the realistic topologies used in our evaluations. Their contributions were invaluable to the success of this project.

For more details, please refer to our paper: [A Practical Near Optimal Deployment of Service Function Chains in Edge-to-Cloud Networks](https://doi.org/10.48550/arXiv.2401.07611).
