from collections import defaultdict
import json
import ast

paths = []
k = 0
k_stop = 2

j_stop = 1

hierarchical = True

LINKS = 'T2_Topologies/25_CRs_links_LC.json'
NODES = 'T2_Topologies/25_CRs_nodes_LC.json'


def find_latency(p):
    with open(LINKS) as json_file:
        data = json.load(json_file)
        json_links = data["links"]
        soma = 0
        for i in range(len(p)-1):
            for link in json_links:
                source_node = link["fromNode"]
                destination_node = link["toNode"]
                if source_node == p[i] and destination_node == p[i+1]:
                    soma = soma + link["delay"]
                    break
        return soma


def ordenate_paths(lp):
    ordenated_lp = []
    distinct_rus = list(set([x[-1] for x in lp]))
    for dru in distinct_rus:
        list_paths_ru = [(x, find_latency(x)) for x in lp if x[-1]==dru]
        ordenated_lp = ordenated_lp + [x[0] for x in sorted(list_paths_ru, key=lambda tup: tup[1])][0:k_stop]
    return ordenated_lp


class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = defaultdict(list)

    def addEdge(self, u, v):
        self.graph[u].append(v)

    def printAllPathsUtil(self, u, d, visited, path):
        visited[u] = True
        path.append(u)
        if u == d:
            if len(path) > 3 and 1 in path and 2 in path:
                pass
            else:
                global k
                k += 1
                if k < k_stop + 1:
                    p = str(path)
                    p = ast.literal_eval(p)
                    paths.append(p)
        else:
            for i in self.graph[u]:
                if visited[i] == False:
                    self.printAllPathsUtil(i, d, visited, path)
        path.pop()
        visited[u] = False

    def printAllPaths(self, s, d):
        visited = [False] * (self.V)
        path = []
        self.printAllPathsUtil(s, d, visited, path)


with open(LINKS) as json_file:
    data = json.load(json_file)
    g = Graph(600)
    json_links = data["links"]
    for item in json_links:
        link = item
        source_node = link["fromNode"]
        destination_node = link["toNode"]
        if source_node < destination_node:
            g.addEdge(source_node, destination_node)
            # ADD THIS CODE FOR T1 TOPOLOGY
            if hierarchical == False:
                g.addEdge(destination_node, source_node)
        else:
            g.addEdge(destination_node, source_node)
            # ADD THIS CODE FOR T1 TOPOLOGY
            if hierarchical == False:
                g.addEdge(source_node, destination_node)
    dst = []
    with open(NODES) as dst_file:
        json_dst = json.load(dst_file)
        nodes = json_dst["nodes"]
        for item in nodes:
            if item["RU"]:
                dst.append(item["nodeNumber"])
    for destination_node in dst:
        k = 0
        g.printAllPaths(0, destination_node)


#paths = ordenate_paths(paths)


with open('paths.json', 'w') as json_file:
    data = {}
    data["paths"] = {}
    path_data = {}
    seq = []
    count = 2
    id = 1

    #------------------------------------------------------------#
    for path in paths:
        for position in range(0, len(path) - 1):
            if position == count:
                for position_cu in range(1, position):
                    p1 = []
                    seq.append(path[position_cu])
                    for i in range(0, position_cu):
                        if i != position:
                            edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                            p1.append(edge)
                    seq.append(path[position])
                    p2 = []
                    for i in range(position_cu, position):
                        if i != position:
                            edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                            p2.append(edge)
                        if i + 1 == position:
                            break
                    seq.append(path[len(path) - 1])
                    p3 = []
                    for i in range(position, len(path) - 1):
                        if i != len(path) - 1:
                            edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                            p3.append(edge)
                        if i + 1 == position:
                            break
                    mec = -1
                    j = 1
                    for position_mec in reversed(range(1, position_cu+1)):
                        if j <= j_stop:
                            p0 = []
                            mec = path[position_mec]
                            for i in range(position_mec, position_cu):
                                if i != position:
                                    edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                                    p0.append(edge)
                            p = {}
                            p["id"] = id
                            p["source"] = "CN"
                            p["target"] = path[len(path) - 1]
                            p["seq"] = seq
                            p["mec"] = mec
                            p["p1"] = p1
                            p["p2"] = p2
                            p["p3"] = p3
                            p["p_mec"] = p0
                            append = True
                            if path_data:
                                for i in path_data:
                                    p_i = path_data[i]
                                    if p_i:
                                        if p_i["p1"] == p["p1"] and p_i["p2"] == p["p2"] and p_i["p3"] == p["p3"] and p_i["p_mec"] == p["p_mec"] and p_i["id"] != \
                                                p["id"]:
                                            append = False
                            if append:
                                path_data["path-{}".format(str(id))] = p
                                id += 1
                            j = j + 1
                    seq = []
                count += 1
        count = 2


    #------------------------------------------------------------#
    count = 1
    for path in paths:
        for position in range(0, len(path) - 1):
            if position == count:
                seq.append(path[0])
                p1 = []
                seq.append(path[position])
                p2 = []
                for i in range(0, len(path) - 1):
                    if i != position:
                        edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                        p2.append(edge)
                    if i + 1 == position:
                        break
                seq.append(path[len(path) - 1])
                p3 = []
                for i in range(position, len(path) - 1):
                    if i != len(path) - 1:
                        edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                        p3.append(edge)
                    if i + 1 == position:
                        break
                mec = -1
                j = 1
                for position_mec in reversed(range(1, position+1)):
                    if j <= j_stop:
                        p0 = []
                        mec = path[position_mec]
                        for i in range(position_mec, position):
                            if i != position:
                                edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                                p0.append(edge)
                        p = {}
                        p["id"] = id
                        p["source"] = "CN"
                        p["target"] = path[len(path) - 1]
                        p["seq"] = seq
                        p['mec'] = mec
                        p["p1"] = p1
                        p["p2"] = p2
                        p["p3"] = p3
                        p["p_mec"] = p0
                        append = True
                        if path_data:
                            for i in path_data:
                                p_i = path_data[i]
                                if p_i:
                                    if p_i["p1"] == p["p1"] and p_i["p2"] == p["p2"] and p_i["p3"] == p["p3"] and p_i["p_mec"] == p["p_mec"]:
                                        append = False
                        if append:
                            #print('teste',p)
                            path_data["path-{}".format(str(id))] = p
                            id += 1
                        j = j + 1
                count += 1
            seq = []
        count = 1


    #------------------------------------------------------------#
    for path in paths:
        seq.append(0)
        p1 = []
        seq.append(0)
        p2 = []
        seq.append(path[len(path) - 1])
        p3 = []
        for i in range(0, len(path) - 1):
            if i != len(path) - 1:
                edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                p3.append(edge)
            if i + 1 == (len(path) - 1):
                break
        mec = -1
        j = 1
        for position_mec in reversed(range(1, len(path))):
            if j <= j_stop:
                p0 = []
                mec = path[position_mec]
                for i in range(position_mec, len(path)-1):
                    if i != len(path)-1:
                        edge = "({}, {})".format(str(path[i]), str(path[i + 1]))
                        p0.append(edge)
                p = {}
                p["id"] = id
                p["source"] = "CN"
                p["target"] = path[len(path) - 1]
                p["seq"] = seq
                p['mec'] = mec
                p["p1"] = p1
                p["p2"] = p2
                p["p3"] = p3
                p["p_mec"] = p0
                append = True
                if path_data:
                    for i in path_data:
                        p_i = path_data[i]
                        if p_i:
                            if p_i["p1"] == p["p1"] and p_i["p2"] == p["p2"] and p_i["p3"] == p["p3"] and p_i["p_mec"] == p["p_mec"] and p_i["id"] != p["id"]:
                                append = False
                if append:
                    path_data["path-{}".format(str(id))] = p
                    id += 1

                j = j + 1
        seq = []
    #------------------------------------------------------------#


    data["paths"] = path_data
    sum = 0
    for iten in path_data:
        sum += 1
    print("{} paths configurations successfully found".format(sum))
    json.dump(data, json_file, indent=4)
