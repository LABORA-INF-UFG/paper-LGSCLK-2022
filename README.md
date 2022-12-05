# Efficient allocation of disaggregated RAN functions and Multi-access Edge Computing services

## Description
This repository contains the model proposed in the work **Efficient allocation of disaggregated RAN functions and Multi-access Edge Computing services**, in addition to the results obtained and the scenario taken into account for the resolution of the proposed problem.

In this work we present a model to solve the MEC service and virtualized RAN functions (vRAN) allocation problem, 
considering the possibility of splitting the data flow into several paths, with the objective of minimize the latency of the services and maximize the centralization of the vRAN.


- [Scenario](#Scenario)
- [Final Results](#final-results)

## Scenario 
We implement our model using Python 3.6.9, docplex 2.20.204 and the IBM optimizer CPLEX 20.1.0. The experiments where performed in a Virtual Machine (VM) with Ubuntu 18.04, 16 vCPUs and 256 GB RAM. The VM is hosted in a server DELL PowerEdge M620 with two Intel Xeon E5-2650 @ 2 GHz.

Two RAN topologies were used to evaluate the model, a traditional
ring-based network (T1) and a next-generation hierarchical RAN (T2), as show in the figure below. For T2 the experiments where performed with topologies with 32, 48, 64, 96, 128, 192 and 256 nodes. For T1 the experiments where performed with topologies with 30 nodes.


![topo_fig](https://github.com/LABORA-INF-UFG/paper-LGSCLK-2022/blob/main/topologies.png)


## Final Results
The results for the proposed solution are available [here](results/), and can also be generated from the execution of the models presented [here](model/).

## Citation

```
@INPROCEEDINGS{Gbc2022MECvRAN,
  title={Efficient allocation of disaggregated RAN functions and Multi-access Edge Computing services},
  author={Fraga, Luciano and De Almeida, Gabriel Matheus Faria and Correa, Sand and Both, Cristiano Bonato and Pinto, Leizer Lima and Cardoso, Kleber},
  booktitle={2022 IEEE Global Communications Conference (GLOBECOM)}, 
  volume={},
  number={},
  pages={forthcoming},
  year={2022}
}
```
