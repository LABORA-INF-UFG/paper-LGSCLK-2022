# -*- coding: utf-8 -*-
import time
import json
from docplex.mp.model import Model
import sys
from util import data_generator, Graph
import argparse
import multiprocessing
import random
import os
import signal

LINKS = '../topologies/T2_Topologies/25_CRs_links_LC.json'
NODES = '../topologies/T2_Topologies/25_CRs_nodes_LC.json'
data_file = '../results/graficos/heuristic_model_dados.json'

hierarchical = True
experiment_time = 240
iteration_time = 100

MEC_load = 0.01
MEC_proc = 100

d_function_limit = 0
worsening_limit = 100

class Path:
    def __init__(self, id, source, target, seq, p1, p2, p3, delay_p1, delay_p2, delay_p3, mec_loc, p_mec, delay_p_mec):
        self.id = id
        self.source = source
        self.target = target
        self.seq = seq
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.delay_p1 = delay_p1
        self.delay_p2 = delay_p2
        self.delay_p3 = delay_p3
        self.mec_loc = mec_loc
        self.p_mec = p_mec
        self.delay_p_mec = delay_p_mec

    def __str__(self):
        return "ID: {}\tSEQ: {}\t P1: {}\t P2: {}\t P3: {}\t dP1: {}\t dP2: {}\t dP3: {}\t mec_loc: {}\t PM: {}\t dPM: {}".format(self.id, self.seq,
                                                                                                 self.p1, self.p2,
                                                                                                 self.p3, self.delay_p1,
                                                                                                 self.delay_p2,
                                                                                                 self.delay_p3,
                                                                                                 self.mec_loc,
                                                                                                 self.p_mec,
                                                                                                 self.delay_p_mec)


class CR:
    def __init__(self, id, cpu, num_BS):
        self.id = id
        self.cpu = cpu
        self.num_BS = num_BS
        # self.ram = ram

    def __str__(self):
        return "ID: {}\tCPU: {}".format(self.id, self.cpu)


class DRC:
    def __init__(self, id, cpu_CU, cpu_DU, cpu_RU, ram_CU, ram_DU, ram_RU, Fs_MEC, Fs_CU, Fs_DU, Fs_RU, delay_BH, delay_MH,
                 delay_FH, bw_BH, bw_MH, bw_FH, q_CRs, cpu_MEC, bw_BH_MEC):
        self.id = id

        self.cpu_CU = cpu_CU
        self.ram_CU = ram_CU
        self.Fs_CU = Fs_CU

        self.cpu_DU = cpu_DU
        self.ram_DU = ram_DU
        self.Fs_DU = Fs_DU

        self.cpu_RU = cpu_RU
        self.ram_RU = ram_RU
        self.Fs_RU = Fs_RU

        self.delay_BH = delay_BH
        self.delay_MH = delay_MH
        self.delay_FH = delay_FH

        self.bw_BH = bw_BH
        self.bw_MH = bw_MH
        self.bw_FH = bw_FH

        self.q_CRs = q_CRs

        self.cpu_MEC = cpu_MEC
        self.bw_BH_MEC = bw_BH_MEC
        self.Fs_MEC = Fs_MEC


class FS:
    def __init__(self, id, f_cpu, f_ram):
        self.id = id
        self.f_cpu = f_cpu
        self.f_ram = f_ram


class RU:
    def __init__(self, id, CR):
        self.id = id
        self.CR = CR

    def __str__(self):
        return "RU: {}\tCR: {}".format(self.id, self.CR)


# Global vars
links = []
capacity = {}
delay = {}
crs = {}
paths = {}
conj_Fs = {}


def read_topology():
    with open(LINKS) as json_file:
        data = json.load(json_file)
        json_links = data["links"]
        for item in json_links:
            link = item
            source_node = link["fromNode"]
            destination_node = link["toNode"]
            if source_node < destination_node:
                capacity[(source_node, destination_node)] = link["capacity"]
                delay[(source_node, destination_node)] = link["delay"]
                links.append((source_node, destination_node))
                # ADD THIS CODE FOR T1 TOPOLOGY
                if hierarchical == False:
                    capacity[(destination_node, source_node)] = link["capacity"]
                    delay[(destination_node, source_node)] = link["delay"]
                    links.append((destination_node, source_node))
            else:
                capacity[(destination_node, source_node)] = link["capacity"]
                delay[(destination_node, source_node)] = link["delay"]
                links.append((destination_node, source_node))
                # ADD THIS CODE FOR T1 TOPOLOGY
                if hierarchical == False:
                    capacity[(source_node, destination_node)] = link["capacity"]
                    delay[(source_node, destination_node)] = link["delay"]
                    links.append((source_node, destination_node))
        with open(NODES) as json_file:
            data = json.load(json_file)
            json_nodes = data["nodes"]
            for item in json_nodes:
                node = item
                CR_id = node["nodeNumber"]
                node_CPU = node["cpu"]
                cr = CR(CR_id, node_CPU, 0)
                crs[CR_id] = cr
        crs[0] = CR(0, 0, 0)
        with open('paths.json') as json_paths_file:
            json_paths_f = json.load(json_paths_file)
            json_paths = json_paths_f["paths"]
            for item in json_paths:
                path = json_paths[item]
                path_id = path["id"]
                path_source = path["source"]
                if path_source == "CN":
                    path_source = 0
                path_target = path["target"]
                path_seq = path["seq"]
                mec_loc = path["mec"]                   #localização do serv. mec
                paths_p = [path["p1"], path["p2"], path["p3"], path["p_mec"]]
                list_p1 = []
                list_p2 = []
                list_p3 = []
                list_p_mec = []
                for path_p in paths_p:
                    aux = ""
                    sum_delay = 0
                    for tup in path_p:
                        aux += tup
                        tup_aux = tup
                        tup_aux = tup_aux.replace('(', '')
                        tup_aux = tup_aux.replace(')', '')
                        tup_aux = tuple(map(int, tup_aux.split(', ')))
                        if path_p == path["p1"]:
                            list_p1.append(tup_aux)
                        elif path_p == path["p2"]:
                            list_p2.append(tup_aux)
                        elif path_p == path["p3"]:
                            list_p3.append(tup_aux)
                        elif path_p == path["p_mec"]:
                            list_p_mec.append(tup_aux)          #lista de links do caminho mec
                        sum_delay += delay[tup_aux]
                    if path_p == path["p1"]:
                        delay_p1 = sum_delay
                    elif path_p == path["p2"]:
                        delay_p2 = sum_delay
                    elif path_p == path["p3"]:
                        delay_p3 = sum_delay
                    elif path_p == path["p_mec"]:
                        delay_p_mec = sum_delay                 #delay do caminho mec
                    if path_seq[0] == 0:
                        delay_p1 = 0
                    if path_seq[1] == 0:
                        delay_p2 = 0
                    if path["mec"] == path_seq[0] or path["mec"] == path_seq[1] or path["mec"] == path_seq[2]:
                        delay_p_mec = 0
                p = Path(path_id, path_source, path_target, path_seq, list_p1, list_p2, list_p3, delay_p1, delay_p2,
                         delay_p3, mec_loc, list_p_mec, delay_p_mec)
                paths[path_id] = p


def DRC_structure_T2():
    DRC1 = DRC(1, 0.49, 2.058, 2.352, 0.01, 0.01, 0.01, [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 9.9, 13.2, 42.6, 3, 0, 0)#1
    DRC2 = DRC(2, 0.98, 1.568, 2.352, 0.01, 0.01, 0.01, [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 9.9, 13.2, 42.6, 3, 0, 0)#2
    DRC4 = DRC(4, 0.49, 1.225, 3.185, 0.01, 0.01, 0.01, [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 9.9, 13.2, 13.6, 3, 0, 0)#7
    DRC5 = DRC(5, 0.98, 0.735, 3.185, 0.01, 0.01, 0.01, [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 9.9, 13.2, 13.6, 3, 0, 0)#8
    DRC6 = DRC(6, 0, 0.49, 4.41, 0, 0.01, 0.01, [0], [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 9.9, 13.2, 2, 0, 0)#12
    DRC7 = DRC(7, 0, 0.98, 3.92, 0, 0.01, 0.01, [0], [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 9.9, 13.2, 2, 0, 0)#13
    DRC8 = DRC(8, 0, 0, 4.9, 0, 0, 0.01, [0], [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 0, 10, 0, 0, 9.9, 1, 0, 0)#19
    DRC9 = DRC(9, 0, 2.54, 2.354, 0, 0.01, 0.01, [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 0, 10, 0.25, 0, 9.9, 42.6, 2, 0, 0)#18
    DRC10 = DRC(10, 0, 1.71, 3.185, 0, 0.01, 0.01, [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 0, 10, 0.25, 0, 9.9, 13.6, 2, 0, 0)#17


    DRC1_B = DRC(1, 0.49, 2.058, 2.352, 0.01, 0.01, 0.01, [0], ['fb', 'f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 42.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC2_B = DRC(2, 0.98, 1.568, 2.352, 0.01, 0.01, 0.01, [0], ['fb', 'f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 42.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC4_B = DRC(4, 0.49, 1.225, 3.185, 0.01, 0.01, 0.01, [0], ['fb', 'f8'], ['f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 13.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC5_B = DRC(5, 0.98, 0.735, 3.185, 0.01, 0.01, 0.01, [0], ['fb', 'f8', 'f7'], ['f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 13.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC6_B = DRC(6, 0, 0.49, 4.41, 0, 0.01, 0.01, [0], [0], ['fb', 'f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 9.9, 13.2 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)
    DRC7_B = DRC(7, 0, 0.98, 3.92, 0, 0.01, 0.01, [0], [0], ['fb', 'f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 9.9, 13.2 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)
    DRC8_B = DRC(8, 0, 0, 4.9, 0, 0, 0.01, [0], [0], [0], ['fb', 'f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 0, 10, 0, 0, 9.9, 1, MEC_proc*MEC_load, MEC_load)
    DRC9_B = DRC(9, 0, 2.548, 2.354, 0, 0.01, 0.01, [0], [0], ['fb', 'f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 0, 10, 0.25, 0, 9.9, 42.6 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)
    DRC10_B = DRC(10, 0, 1.715, 3.185, 0, 0.01, 0.01, [0], [0], ['fb', 'f8', 'f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 0, 10, 0.25, 0, 9.9, 13.6 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)


    DRC1_C = DRC(1, 0.49, 2.058, 2.352, 0.01, 0.01, 0.01, ['fb'], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 42.6 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC2_C = DRC(2, 0.98, 1.568, 2.352, 0.01, 0.01, 0.01, ['fb'], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 42.6 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC4_C = DRC(4, 0.49, 1.225, 3.185, 0.01, 0.01, 0.01, ['fb'], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 13.6 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC5_C = DRC(5, 0.98, 0.735, 3.185, 0.01, 0.01, 0.01, ['fb'], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 9.9, 13.2 + MEC_load, 13.6 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC6_C = DRC(6, 0, 0.49, 4.41, 0, 0.01, 0.01, ['fb'], [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 9.9, 13.2 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC7_C = DRC(7, 0, 0.98, 3.92, 0, 0.01, 0.01, ['fb'], [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 9.9, 13.2 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC8_C = DRC(8, 0, 0, 4.9, 0, 0, 0.01, ['fb'], [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 0, 10, 0, 0, 9.9, 2, MEC_proc*MEC_load, MEC_load)
    DRC9_C = DRC(9, 0, 2.548, 2.354, 0, 0.01, 0.01, ['fb'], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 0, 10, 0.25, 0, 9.9, 42.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC10_C = DRC(10, 0, 1.715, 3.185, 0, 0.01, 0.01, ['fb'], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 0, 10, 0.25, 0, 9.9, 13.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)

    DRCs = {1: DRC1, 2: DRC2, 4: DRC4, 5: DRC5, 6: DRC6, 7: DRC7, 8: DRC8, 9: DRC9, 10: DRC10,
            11: DRC1_B, 12: DRC2_B, 14: DRC4_B, 15: DRC5_B, 16: DRC6_B, 17:DRC7_B, 18: DRC8_B, 19: DRC9_B, 20: DRC10_B,
            21: DRC1_C, 22: DRC2_C, 24: DRC4_C, 25: DRC5_C, 26: DRC6_C, 27:DRC7_C, 28: DRC8_C, 29: DRC9_C, 30: DRC10_C}

    return DRCs




def DRC_structure_T1():
    DRC1 = DRC(1, 0.49, 2.058, 2.352, 0.01, 0.01, 0.01, [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 3, 5.4, 17.4, 3, 0, 0)#1
    DRC2 = DRC(2, 0.98, 1.568, 2.352, 0.01, 0.01, 0.01, [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 3, 5.4, 17.4, 3, 0, 0)#2
    DRC4 = DRC(4, 0.49, 1.225, 3.185, 0.01, 0.01, 0.01, [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 3, 5.4, 5.6, 3, 0, 0)#7
    DRC5 = DRC(5, 0.98, 0.735, 3.185, 0.01, 0.01, 0.01, [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 3, 5.4, 5.6, 3, 0, 0)#8
    DRC6 = DRC(6, 0, 0.49, 4.41, 0, 0.01, 0.01, [0], [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 3, 5.4, 2, 0, 0)#12
    DRC7 = DRC(7, 0, 0.98, 3.92, 0, 0.01, 0.01, [0], [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 3, 5.4, 2, 0, 0)#13
    DRC8 = DRC(8, 0, 0, 4.9, 0, 0, 0.01, [0], [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 0, 10, 0, 0, 3, 1, 0, 0)#19
    DRC9 = DRC(9, 0, 2.54, 2.354, 0, 0.01, 0.01, [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 0, 10, 0.25, 0, 3, 17.4, 2, 0, 0)#18
    DRC10 = DRC(10, 0, 1.71, 3.185, 0, 0.01, 0.01, [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 0, 10, 0.25, 0, 3, 5.6, 2, 0, 0)#17


    DRC1_B = DRC(1, 0.49, 2.058, 2.352, 0.01, 0.01, 0.01, [0], ['fb', 'f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 17.4 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC2_B = DRC(2, 0.98, 1.568, 2.352, 0.01, 0.01, 0.01, [0], ['fb', 'f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 17.4 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC4_B = DRC(4, 0.49, 1.225, 3.185, 0.01, 0.01, 0.01, [0], ['fb', 'f8'], ['f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 5.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC5_B = DRC(5, 0.98, 0.735, 3.185, 0.01, 0.01, 0.01, [0], ['fb', 'f8', 'f7'], ['f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 5.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC6_B = DRC(6, 0, 0.49, 4.41, 0, 0.01, 0.01, [0], [0], ['fb', 'f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 3, 5.4 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)
    DRC7_B = DRC(7, 0, 0.98, 3.92, 0, 0.01, 0.01, [0], [0], ['fb', 'f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 3, 5.4 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)
    DRC8_B = DRC(8, 0, 0, 4.9, 0, 0, 0.01, [0], [0], [0], ['fb', 'f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 0, 10, 0, 0, 3, 1, MEC_proc*MEC_load, MEC_load)
    DRC9_B = DRC(9, 0, 2.548, 2.354, 0, 0.01, 0.01, [0], [0], ['fb', 'f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 0, 10, 0.25, 0, 3, 17.4 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)
    DRC10_B = DRC(10, 0, 1.715, 3.185, 0, 0.01, 0.01, [0], [0], ['fb', 'f8', 'f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 0, 10, 0.25, 0, 3, 5.6 + MEC_load, 2, MEC_proc*MEC_load, MEC_load)


    DRC1_C = DRC(1, 0.49, 2.058, 2.352, 0.01, 0.01, 0.01, ['fb'], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 17.4 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC2_C = DRC(2, 0.98, 1.568, 2.352, 0.01, 0.01, 0.01, ['fb'], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 17.4 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC4_C = DRC(4, 0.49, 1.225, 3.185, 0.01, 0.01, 0.01, ['fb'], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 5.6 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC5_C = DRC(5, 0.98, 0.735, 3.185, 0.01, 0.01, 0.01, ['fb'], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 10, 10, 0.25, 3, 5.4 + MEC_load, 5.6 + MEC_load, 4, MEC_proc*MEC_load, MEC_load)
    DRC6_C = DRC(6, 0, 0.49, 4.41, 0, 0.01, 0.01, ['fb'], [0], ['f8'], ['f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 3, 5.4 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC7_C = DRC(7, 0, 0.98, 3.92, 0, 0.01, 0.01, ['fb'], [0], ['f8', 'f7'], ['f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 10, 10, 0, 3, 5.4 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC8_C = DRC(8, 0, 0, 4.9, 0, 0, 0.01, ['fb'], [0], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2', 'f1', 'f0'], 0, 0, 10, 0, 0, 3, 2, MEC_proc*MEC_load, MEC_load)
    DRC9_C = DRC(9, 0, 2.548, 2.354, 0, 0.01, 0.01, ['fb'], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3', 'f2'], ['f1', 'f0'], 0, 10, 0.25, 0, 3, 17.4 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)
    DRC10_C = DRC(10, 0, 1.715, 3.185, 0, 0.01, 0.01, ['fb'], [0], ['f8', 'f7', 'f6', 'f5', 'f4', 'f3'], ['f2', 'f1', 'f0'], 0, 10, 0.25, 0, 3, 5.6 + MEC_load, 3, MEC_proc*MEC_load, MEC_load)

    DRCs = {1: DRC1, 2: DRC2, 4: DRC4, 5: DRC5, 6: DRC6, 7: DRC7, 8: DRC8, 9: DRC9, 10: DRC10,
            11: DRC1_B, 12: DRC2_B, 14: DRC4_B, 15: DRC5_B, 16: DRC6_B, 17:DRC7_B, 18: DRC8_B, 19: DRC9_B, 20: DRC10_B,
            21: DRC1_C, 22: DRC2_C, 24: DRC4_C, 25: DRC5_C, 26: DRC6_C, 27:DRC7_C, 28: DRC8_C, 29: DRC9_C, 30: DRC10_C}

    return DRCs



def RU_location():
    rus = {}
    count = 1
    with open(NODES) as json_file:
        data = json.load(json_file)
        json_crs = data["nodes"]
        for item in json_crs:
            node = item
            num_rus = node["RU"]
            num_cr = node["nodeNumber"]
            for i in range(0, num_rus):
                rus[count] = RU(count, int(num_cr))
                count += 1
    return rus


DRC_f1 = 0
f0_vars = []
f1_vars = []
f2_vars = []


def MEC_location():

    mec = []

    with open(NODES) as json_file:
        data = json.load(json_file)

        json_crs = data["nodes"]

        for item in json_crs:
            node = item
            num_mec = node["MEC"]
            num_cr = node["nodeNumber"]
            # Creates the RUs
            if num_mec >=1:
                mec.append(num_cr)

    return mec



def run_stage_0(centralization_points):
    print("Running Stage - 0")
    print("------------------------------------------------------------------------------------------------------------")
    alocation_time_start = time.time()
    read_topology()
    DRCs = DRC_structure_T2() if hierarchical == True else DRC_structure_T1()
    rus = RU_location()
    mec = MEC_location()

    F0 = FS('fb', 2, 2)
    F1 = FS('f8', 2, 2)
    F2 = FS('f7', 2, 2)
    F3 = FS('f6', 2, 2)
    F4 = FS('f5', 2, 2)
    F5 = FS('f4', 2, 2)
    F6 = FS('f3', 2, 2)
    F7 = FS('f2', 2, 2)
    F8 = FS('f1', 2, 2)
    F9 = FS('f0', 2, 2)
    conj_Fs = {'f8': F1, 'f7': F2, 'f6': F3, 'f5': F4, 'f4': F5, 'f3': F6, 'f2': F7}
    mdl = Model(name='NGRAN Problem', log_output=True)
    mdl.parameters.mip.tolerances.mipgap = 0
    mdl.parameters.emphasis.mip = 2

    i = [(p, d, b) for p in paths for d in DRCs for b in rus if (paths[p].seq[2] == rus[b].CR and ((paths[p].seq[0] in centralization_points and paths[p].seq[1] in centralization_points) or (paths[p].seq[0] == 0 and paths[p].seq[1] in centralization_points) or (paths[p].seq[0] == 0 and paths[p].seq[1] == 0))  and (paths[p].mec_loc in centralization_points or paths[p].mec_loc == paths[p].seq[2])) and
                                                                ((d in [1,2,4,5,6,7,8,9,10]  and rus[b].CR not in mec) or (d in [11,12,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30]  and rus[b].CR in mec and
                                                                ((d in [11,12,14,15,16,17,18,19,20] and (paths[p].mec_loc == paths[p].seq[0] or paths[p].mec_loc == paths[p].seq[1] or paths[p].mec_loc == paths[p].seq[2])) or
                                                                 (d in [21,22,24,25,26,27,28,29,30] and (paths[p].mec_loc != paths[p].seq[0] and paths[p].mec_loc != paths[p].seq[1] and paths[p].mec_loc != paths[p].seq[2]))))) and
                                                                ((paths[p].seq[0] != 0 and d in [1,2,4,5,11,12,14,15,21,22,24,25]) or (paths[p].seq[0] == 0 and paths[p].seq[1] != 0 and d in [6,7,9,10,16,17,19,20,26,27,29,30]) or (paths[p].seq[0] == 0 and paths[p].seq[1] == 0 and d in [8,18,28]))]


    mdl.x = mdl.binary_var_dict(keys=i, name='x')
    mdl.y = mdl.continuous_var_dict(keys=i, name='y')


    total_delay = mdl.sum(mdl.max((mdl.x[it]*(paths[it[0]].delay_p_mec + (paths[it[0]].delay_p2*mdl.min(1, paths[it[0]].seq[0])) + (paths[it[0]].delay_p3*mdl.min(1, paths[it[0]].seq[1])) + ((((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load)*0.25 + pow(((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load, 2)*0.25))for it in i if rus[it[2]].CR in mec and b==it[2])) for b in rus if rus[b].CR in mec)

    mdl.minimize(total_delay)

    # CONSTRAINT 0 - Bottom limit of aplication(sum delay d)
    mdl.add_constraint(total_delay>= d_function_limit, 'bottom limit of aplication(delay)')

    for b in rus:
        mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if it[2] == b) >= 1, 'at least one path')
    for p in paths:
        mdl.add_constraint(mdl.sum(mdl.sum(mdl.x[it] for it in i if it[2] == b and it[0] == p) for b in rus) <= 1.0,
                           'path unicity')
    for b in rus:
        mdl.add_constraint(
            mdl.sum(mdl.min(mdl.sum(mdl.x[it] for it in i if it[2] == b and it[1] == d), 1) for d in DRCs) == 1.0, 'no duplicate DRCs to the same RU')
    for b in rus:
        mdl.add_constraint(mdl.sum(mdl.y[it] for it in i if it[2] == b) == 1.0, 'split total')
    for it in i:
        mdl.add_constraint(mdl.y[it] >= 0, 'y_var definition')
    for it in i:
        mdl.add_constraint(mdl.y[it] <= mdl.x[it], 'y_var and x_var match')
    for it in i:
        mdl.add_constraint(mdl.x[it] - mdl.y[it] <= 0.900, 'minimum split y_var')
    for b in rus:
        mdl.add_constraint(mdl.sum(
            mdl.min(1, mdl.sum(mdl.x[it] for it in i if (c in paths[it[0]].seq or c == paths[it[0]].mec_loc) and it[2] == b and c != 0)) for c in
            crs) == mdl.sum(mdl.y[it] * DRCs[it[1]].q_CRs for it in i if it[2] == b), 'no duplicate VNFs')
    for l in links:
        k = (l[1], l[0])
        mdl.add_constraint(mdl.sum(mdl.y[it] * DRCs[it[1]].bw_BH_MEC for it in i if l in paths[it[0]].p_mec or k in paths[it[0]].p_mec)
                           + mdl.sum(mdl.y[it] * DRCs[it[1]].bw_BH for it in i if l in paths[it[0]].p1 or k in paths[it[0]].p1)
                           + mdl.sum(mdl.y[it] * DRCs[it[1]].bw_MH for it in i if l in paths[it[0]].p2 or k in paths[it[0]].p2)
                           + mdl.sum(mdl.y[it] * DRCs[it[1]].bw_FH for it in i if l in paths[it[0]].p3 or k in paths[it[0]].p3)
                           <= capacity[l], 'links_bw')
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if paths[it[0]].target != rus[it[2]].CR) == 0, 'path')

    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] != 0 and (it[1] == 6 or it[1] == 16 or it[1] == 26 or it[1] == 7 or it[1] == 17 or it[1] == 27 or 
        it[1] == 8 or it[1] == 18 or it[1] == 28 or it[1] == 9 or it[1] == 19 or it[1] == 29 or it[1] == 10 or it[1] == 20 or it[1] == 30)) == 0, 'DRCs_path_pick')

    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] == 0 and it[1] != 6 and it[1] != 16 and it[1] != 26 and it[1] != 7 and it[1] != 17 and it[1] != 27 and 
        it[1] != 8 and it[1] != 18 and it[1] != 28 and it[1] != 9 and it[1] != 19 and it[1] != 29 and it[1] != 10 and it[1] != 20 and it[1] != 30) == 0, 'DRCs_path_pick2')

    mdl.add_constraint(
        mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] == 0 and paths[it[0]].seq[1] == 0 and it[1] != 8 and it[1] != 18 and it[1] != 28) == 0,
        'DRCs_path_pick3')

    mdl.add_constraint(
        mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] == 0 and paths[it[0]].seq[1] != 0 and (it[1] == 8 or it[1] == 18 or it[1] == 28)) == 0,
        'DRCs_path_pick4')

    for ru in rus:
        mdl.add_constraint(
            mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[2] != rus[ru].CR and it[2] == rus[ru].id) == 0, 'path destination')
    for it in i:
        mdl.add_constraint((mdl.x[it] * paths[it[0]].delay_p1) <= DRCs[it[1]].delay_BH, 'delay_req_p1')
    for it in i:
        mdl.add_constraint((mdl.x[it] * paths[it[0]].delay_p2) <= DRCs[it[1]].delay_MH, 'delay_req_p2')
    for it in i:
        mdl.add_constraint((mdl.x[it] * paths[it[0]].delay_p3 <= DRCs[it[1]].delay_FH), 'delay_req_p3')
    for c in crs:
        mdl.add_constraint(mdl.sum(mdl.sum(mdl.min(DRCs[D].cpu_MEC, mdl.sum(mdl.x[it] * DRCs[D].cpu_MEC for it in i if
                                                                           c == paths[it[0]].mec_loc and it[2] == b and
                                                                           it[1] == D)) + 
                                            mdl.min(DRCs[D].cpu_CU, mdl.sum(mdl.x[it] * DRCs[D].cpu_CU for it in i if
                                                                           c == paths[it[0]].seq[0] and it[2] == b and
                                                                           it[1] == D)) + mdl.min(DRCs[D].cpu_DU,
                                                                                                  mdl.sum(
                                                                                                      mdl.x[it] * DRCs[
                                                                                                          D].cpu_DU for
                                                                                                      it in i if c ==
                                                                                                      paths[it[0]].seq[
                                                                                                          1] and it[
                                                                                                          2] == b and
                                                                                                      it[
                                                                                                          1] == D)) + mdl.min(
            DRCs[D].cpu_RU,
            mdl.sum(mdl.x[it] * DRCs[D].cpu_RU for it in i if c == paths[it[0]].seq[2] and it[2] == b and it[1] == D))
                                           for D in DRCs) for b in rus) <= crs[c].cpu, 'crs_cpu_usage')

    # Restrições de desativação de DRCs principais para RUs com demanda MEC e assegurar que DRCs agregadas não escolham caminhos onde o serv. mec esteja desagregado de seq
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if (it[1] in [1,2,4,5,6,7,8,9,10,11,12,14,15,16,17,18,19,20]) and 
        (paths[it[0]].mec_loc != paths[it[0]].seq[0] and paths[it[0]].mec_loc != paths[it[0]].seq[1] and paths[it[0]].mec_loc != paths[it[0]].seq[2]) and rus[it[2]].CR in mec) == 0, 'path')

    # Restrições de desativação de DRCs principais para RUs com demanda MEC e assegurar que DRCs desagregadas não escolham caminhos onde o serv. mec esteja agregado a seq
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if (it[1] in [1,2,4,5,6,7,8,9,10,21,22,24,25,26,27,28,29,30]) and 
        (paths[it[0]].mec_loc == paths[it[0]].seq[0] or paths[it[0]].mec_loc == paths[it[0]].seq[1] or paths[it[0]].mec_loc == paths[it[0]].seq[2]) and rus[it[2]].CR in mec) == 0, 'path')

    # Restrições de desativação de DRCs MEC para RUs sem demanda MEC
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if it[1] in [11,12,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30] and rus[it[2]].CR not in mec) == 0, 'path')

    alocation_time_end = time.time()
    start_time = time.time()
    mdl.solve()
    end_time = time.time()
    print("Stage 0 - Alocation Time: {}".format(alocation_time_end - alocation_time_start))
    print("Stage 0 - Enlapsed Time: {}".format(end_time - start_time))
    for it in i:
        if mdl.x[it].solution_value > 0:
            print("x{} -> {}".format(it, mdl.x[it].solution_value))
            print(paths[it[0]].seq)
    for it in i:
        if mdl.y[it].solution_value > 0:
            print("y{} -> {}".format(it, mdl.y[it].solution_value))
    disp_Fs = {}
    for cr in crs:
        disp_Fs[cr] = {'fb': 0, 'f8': 0, 'f7': 0, 'f6': 0, 'f5': 0, 'f4': 0, 'f3': 0, 'f2': 0, 'f1': 0, 'f0': 0}
    for it in i:
        for cr in crs:
            if mdl.x[it].solution_value > 0:
                if cr in paths[it[0]].seq or cr == paths[it[0]].mec_loc:
                    seq = paths[it[0]].seq
                    if cr == paths[it[0]].mec_loc:
                        Fs = DRCs[it[1]].Fs_MEC
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
                    if cr == seq[0]:
                        Fs = DRCs[it[1]].Fs_CU
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
                    if cr == seq[1]:
                        Fs = DRCs[it[1]].Fs_DU
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
                    if cr == seq[2]:
                        Fs = DRCs[it[1]].Fs_RU
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
    print("FO: {}".format(mdl.solution.get_objective_value()))
    for cr in disp_Fs:
        print(str(cr) + str(disp_Fs[cr]))
    global f0_vars
    for it in i:
        if mdl.x[it].solution_value > 0:
            f0_vars.append(it)
    return mdl.solution.get_objective_value()




def run_stage_1(FO_Stage_0, centralization_points, ksv, best_solution):
    print("Running Stage - 1")
    print("------------------------------------------------------------------------------------------------------------")
    alocation_time_start = time.time()
    read_topology()
    DRCs = DRC_structure_T2() if hierarchical == True else DRC_structure_T1()
    rus = RU_location()
    mec = MEC_location()

    F0 = FS('fb', 2, 2)
    F1 = FS('f8', 2, 2)
    F2 = FS('f7', 2, 2)
    F3 = FS('f6', 2, 2)
    F4 = FS('f5', 2, 2)
    F5 = FS('f4', 2, 2)
    F6 = FS('f3', 2, 2)
    F7 = FS('f2', 2, 2)
    F8 = FS('f1', 2, 2)
    F9 = FS('f0', 2, 2)
    conj_Fs = {'f8': F1, 'f7': F2, 'f6': F3, 'f5': F4, 'f4': F5, 'f3': F6, 'f2': F7}
    mdl = Model(name='NGRAN Problem', log_output=True)
    #mdl.parameters.mip.tolerances.mipgap = 0
    mdl.parameters.mip.tolerances.absmipgap = 1
    mdl.parameters.emphasis.mip = 2
    mdl.parameters.timelimit = iteration_time


    i = [(p, d, b) for p in paths for d in DRCs for b in rus if (paths[p].seq[2] == rus[b].CR and ((paths[p].seq[0] in centralization_points and paths[p].seq[1] in centralization_points) or (paths[p].seq[0] == 0 and paths[p].seq[1] in centralization_points) or (paths[p].seq[0] == 0 and paths[p].seq[1] == 0))  and (paths[p].mec_loc in centralization_points or paths[p].mec_loc == paths[p].seq[2])) and
                                                                ((d in [1,2,4,5,6,7,8,9,10]  and rus[b].CR not in mec) or (d in [11,12,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30]  and rus[b].CR in mec and
                                                                ((d in [11,12,14,15,16,17,18,19,20] and (paths[p].mec_loc == paths[p].seq[0] or paths[p].mec_loc == paths[p].seq[1] or paths[p].mec_loc == paths[p].seq[2])) or
                                                                 (d in [21,22,24,25,26,27,28,29,30] and (paths[p].mec_loc != paths[p].seq[0] and paths[p].mec_loc != paths[p].seq[1] and paths[p].mec_loc != paths[p].seq[2]))))) and
                                                                ((paths[p].seq[0] != 0 and d in [1,2,4,5,11,12,14,15,21,22,24,25]) or (paths[p].seq[0] == 0 and paths[p].seq[1] != 0 and d in [6,7,9,10,16,17,19,20,26,27,29,30]) or (paths[p].seq[0] == 0 and paths[p].seq[1] == 0 and d in [8,18,28]))]

    #print(i)
    mdl.x = mdl.binary_var_dict(keys=i, name='x')
    mdl.y = mdl.continuous_var_dict(keys=i, name='y')
    phy1 = mdl.sum(mdl.min(1, mdl.sum(mdl.x[it] for it in i if c in paths[it[0]].seq or c == paths[it[0]].mec_loc)) for c in crs if crs[c].id != 0)
    phy2 = mdl.sum(mdl.sum(mdl.max(0, mdl.sum(mdl.min(1, mdl.sum(mdl.x[it] for it in i if (
                (paths[it[0]].seq[0] == crs[c].id and it[2] == b and f in DRCs[it[1]].Fs_CU) or (
                    paths[it[0]].seq[1] == crs[c].id and it[2] == b and f in DRCs[it[1]].Fs_DU) or (
                            paths[it[0]].seq[2] == crs[c].id and it[2] == b and f in DRCs[it[1]].Fs_RU)))) for b in
                                              rus) - 1) for f in conj_Fs) for c in crs)
    mdl.minimize(phy1 - phy2)


    total_delay = mdl.sum(mdl.max((mdl.x[it]*(paths[it[0]].delay_p_mec + (paths[it[0]].delay_p2*mdl.min(1, paths[it[0]].seq[0])) + (paths[it[0]].delay_p3*mdl.min(1, paths[it[0]].seq[1])) + ((((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load)*0.25 + pow(((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load, 2)*0.25))for it in i if rus[it[2]].CR in mec and b==it[2])) for b in rus if rus[b].CR in mec)

    #mdl.add_constraint(total_delay <= worsening_limit + FO_Stage_0, 'worsening_limit')

    mdl.add_constraint(total_delay <= worsening_limit, 'worsening_limit')

    # CONSTRAINT 0 - Bottom limit of aplication(sum delay d)
    mdl.add_constraint(total_delay >= d_function_limit, 'bottom limit of aplication(delay)')

    for b in rus:
        mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if it[2] == b) >= 1, 'at least one path')
    for p in paths:
        mdl.add_constraint(mdl.sum(mdl.sum(mdl.x[it] for it in i if it[2] == b and it[0] == p) for b in rus) <= 1.0,
                           'path unicity')
    for b in rus:
        mdl.add_constraint(
            mdl.sum(mdl.min(mdl.sum(mdl.x[it] for it in i if it[2] == b and it[1] == d), 1) for d in DRCs) == 1.0, 'no duplicate DRCs to the same RU')
    for b in rus:
        mdl.add_constraint(mdl.sum(mdl.y[it] for it in i if it[2] == b) == 1.0, 'split total')
    for it in i:
        mdl.add_constraint(mdl.y[it] >= 0, 'y_var definition')
    for it in i:
        mdl.add_constraint(mdl.y[it] <= mdl.x[it], 'y_var and x_var match')
    for it in i:
        mdl.add_constraint(mdl.x[it] - mdl.y[it] <= 0.900, 'minimum split y_var')
    for b in rus:
        mdl.add_constraint(mdl.sum(
            mdl.min(1, mdl.sum(mdl.x[it] for it in i if (c in paths[it[0]].seq or c == paths[it[0]].mec_loc) and it[2] == b and c != 0)) for c in
            crs) == mdl.sum(mdl.y[it] * DRCs[it[1]].q_CRs for it in i if it[2] == b), 'no duplicate VNFs')
    for l in links:
        k = (l[1], l[0])
        mdl.add_constraint(mdl.sum(mdl.y[it] * DRCs[it[1]].bw_BH_MEC for it in i if l in paths[it[0]].p_mec or k in paths[it[0]].p_mec)
                           + mdl.sum(mdl.y[it] * DRCs[it[1]].bw_BH for it in i if l in paths[it[0]].p1 or k in paths[it[0]].p1)
                           + mdl.sum(mdl.y[it] * DRCs[it[1]].bw_MH for it in i if l in paths[it[0]].p2 or k in paths[it[0]].p2)
                           + mdl.sum(mdl.y[it] * DRCs[it[1]].bw_FH for it in i if l in paths[it[0]].p3 or k in paths[it[0]].p3)
                           <= capacity[l], 'links_bw')
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if paths[it[0]].target != rus[it[2]].CR) == 0, 'path')

    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] != 0 and (it[1] == 6 or it[1] == 16 or it[1] == 26 or it[1] == 7 or it[1] == 17 or it[1] == 27 or 
        it[1] == 8 or it[1] == 18 or it[1] == 28 or it[1] == 9 or it[1] == 19 or it[1] == 29 or it[1] == 10 or it[1] == 20 or it[1] == 30)) == 0, 'DRCs_path_pick')

    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] == 0 and it[1] != 6 and it[1] != 16 and it[1] != 26 and it[1] != 7 and it[1] != 17 and it[1] != 27 and 
        it[1] != 8 and it[1] != 18 and it[1] != 28 and it[1] != 9 and it[1] != 19 and it[1] != 29 and it[1] != 10 and it[1] != 20 and it[1] != 30) == 0, 'DRCs_path_pick2')

    mdl.add_constraint(
        mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] == 0 and paths[it[0]].seq[1] == 0 and it[1] != 8 and it[1] != 18 and it[1] != 28) == 0,
        'DRCs_path_pick3')

    mdl.add_constraint(
        mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[0] == 0 and paths[it[0]].seq[1] != 0 and (it[1] == 8 or it[1] == 18 or it[1] == 28)) == 0,
        'DRCs_path_pick4')

    for ru in rus:
        mdl.add_constraint(
            mdl.sum(mdl.x[it] for it in i if paths[it[0]].seq[2] != rus[ru].CR and it[2] == rus[ru].id) == 0, 'path destination')
    for it in i:
        mdl.add_constraint((mdl.x[it] * paths[it[0]].delay_p1) <= DRCs[it[1]].delay_BH, 'delay_req_p1')
    for it in i:
        mdl.add_constraint((mdl.x[it] * paths[it[0]].delay_p2) <= DRCs[it[1]].delay_MH, 'delay_req_p2')
    for it in i:
        mdl.add_constraint((mdl.x[it] * paths[it[0]].delay_p3 <= DRCs[it[1]].delay_FH), 'delay_req_p3')
    for c in crs:
        mdl.add_constraint(mdl.sum(mdl.sum(mdl.min(DRCs[D].cpu_MEC, mdl.sum(mdl.x[it] * DRCs[D].cpu_MEC for it in i if
                                                                           c == paths[it[0]].mec_loc and it[2] == b and
                                                                           it[1] == D)) + 
                                            mdl.min(DRCs[D].cpu_CU, mdl.sum(mdl.x[it] * DRCs[D].cpu_CU for it in i if
                                                                           c == paths[it[0]].seq[0] and it[2] == b and
                                                                           it[1] == D)) + mdl.min(DRCs[D].cpu_DU,
                                                                                                  mdl.sum(
                                                                                                      mdl.x[it] * DRCs[
                                                                                                          D].cpu_DU for
                                                                                                      it in i if c ==
                                                                                                      paths[it[0]].seq[
                                                                                                          1] and it[
                                                                                                          2] == b and
                                                                                                      it[
                                                                                                          1] == D)) + mdl.min(
            DRCs[D].cpu_RU,
            mdl.sum(mdl.x[it] * DRCs[D].cpu_RU for it in i if c == paths[it[0]].seq[2] and it[2] == b and it[1] == D))
                                           for D in DRCs) for b in rus) <= crs[c].cpu, 'crs_cpu_usage')

    # Restrições de desativação de DRCs principais para RUs com demanda MEC e assegurar que DRCs agregadas não escolham caminhos onde o serv. mec esteja desagregado de seq
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if (it[1] in [1,2,4,5,6,7,8,9,10,11,12,14,15,16,17,18,19,20]) and 
        (paths[it[0]].mec_loc != paths[it[0]].seq[0] and paths[it[0]].mec_loc != paths[it[0]].seq[1] and paths[it[0]].mec_loc != paths[it[0]].seq[2]) and rus[it[2]].CR in mec) == 0, 'path')

    # Restrições de desativação de DRCs principais para RUs com demanda MEC e assegurar que DRCs desagregadas não escolham caminhos onde o serv. mec esteja agregado a seq
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if (it[1] in [1,2,4,5,6,7,8,9,10,21,22,24,25,26,27,28,29,30]) and 
        (paths[it[0]].mec_loc == paths[it[0]].seq[0] or paths[it[0]].mec_loc == paths[it[0]].seq[1] or paths[it[0]].mec_loc == paths[it[0]].seq[2]) and rus[it[2]].CR in mec) == 0, 'path')

    # Restrições de desativação de DRCs MEC para RUs sem demanda MEC
    mdl.add_constraint(mdl.sum(mdl.x[it] for it in i if it[1] in [11,12,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30] and rus[it[2]].CR not in mec) == 0, 'path')


    warm_start = mdl.new_solution()
    for it in f0_vars:
        warm_start.add_var_value(mdl.x[it], 1)
    mdl.add_mip_start(warm_start)

    alocation_time_end = time.time()
    start_time = time.time()
    mdl.solve()
    end_time = time.time()
    print("Stage 1 - Alocation Time: {}".format(alocation_time_end - alocation_time_start))
    print("Stage 1 - Enlapsed Time: {}".format(end_time - start_time))
    for it in i:
        if mdl.x[it].solution_value > 0:
            print("x{} -> {}".format(it, mdl.x[it].solution_value))
            print(paths[it[0]].seq)
    for it in i:
        if mdl.y[it].solution_value > 0:
            print("y{} -> {}".format(it, mdl.y[it].solution_value))
    disp_Fs = {}
    for cr in crs:
        disp_Fs[cr] = {'fb': 0, 'f8': 0, 'f7': 0, 'f6': 0, 'f5': 0, 'f4': 0, 'f3': 0, 'f2': 0, 'f1': 0, 'f0': 0}
    for it in i:
        for cr in crs:
            if mdl.x[it].solution_value > 0:
                if cr in paths[it[0]].seq or cr == paths[it[0]].mec_loc:
                    seq = paths[it[0]].seq
                    if cr == paths[it[0]].mec_loc:
                        Fs = DRCs[it[1]].Fs_MEC
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
                    if cr == seq[0]:
                        Fs = DRCs[it[1]].Fs_CU
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
                    if cr == seq[1]:
                        Fs = DRCs[it[1]].Fs_DU
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
                    if cr == seq[2]:
                        Fs = DRCs[it[1]].Fs_RU
                        for o in Fs:
                            if o != 0:
                                dct = disp_Fs[cr]
                                dct["{}".format(o)] += 1
                                disp_Fs[cr] = dct
    print("FO: {}".format(mdl.solution.get_objective_value()))
    for cr in disp_Fs:
        print(str(cr) + str(disp_Fs[cr]))




    if mdl.solution.get_objective_value() < best_solution:
        print('############### Best Solution ##################')
        data_generator(mdl, i, FO_Stage_0, worsening_limit, MEC_proc, MEC_load, rus, mec, paths, DRCs, crs, conj_Fs, data_file,  '_best_solution')
        global f1_vars
        for it in i:
            if mdl.x[it].solution_value > 0:
                f1_vars.append(it)
        return (mdl.solution.get_objective_value(), True, mdl.solution.get_objective_value())


    return (mdl.solution.get_objective_value(), False, best_solution)



def execute_iterations():
    best_solution = 1e7
    n = 0
    g = Graph(True)
    g.graph = g.matrix_graph(NODES, LINKS)
    ksv_list = random.sample(range(1, g.V-1), 20)
    print('k_list: ', ksv_list)
    for ksv in ksv_list:
        if n == 3:
            print("################ 3 solutions with no improvements")
            break
        n = n+1
        centralization_points = g.K_shortest_vertices_with_dijkstra(0, ksv)
        print('centralization_points', centralization_points)
        start_all = time.time()
        FO_Stage_0 = run_stage_0(centralization_points)
        FO_Stage_1, status, best_solution = run_stage_1(FO_Stage_0, centralization_points, ksv, best_solution)
        if status == True:
            n = 0
        end_all = time.time()
        print("TOTAL TIME: {}".format(end_all - start_all))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--worsening_limit", help="Value do be add to the optimal value of FO_Stage_0 in FO_Stage_1'")
    args = parser.parse_args()

    if args.worsening_limit:
        print(args.worsening_limit)
        worsening_limit = int(args.worsening_limit)


    p = multiprocessing.Process(target=execute_iterations, name="f0_f1")
    p.start()
    p.join(experiment_time)
    if p.is_alive():
        print("#################################\n")
        print("Time limit of the experiment\n")
        print("#################################")
        os.kill(p.pid, signal.SIGINT)
        print("\n\nProcess will be terminated in 2min...\n\n")
        time.sleep(120)
        print("Terminated")
        p.kill()
        p.join()

