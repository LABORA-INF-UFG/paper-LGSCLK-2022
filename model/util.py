import json


class Graph():

    def __init__(self, hierarchical):
        self.V = None
        self.graph = None
        self.hierarchical = hierarchical

    def minDistance(self, dist, sptSet):
        min = 1e7
        for v in range(self.V):
            if dist[v] < min and sptSet[v] == False:
                min = dist[v]
                min_index = v
        return min_index

    def K_shortest_vertices_with_dijkstra(self, src, k):
        dist = [1e7] * self.V
        dist[src] = 0
        sptSet = [False] * self.V
        for cout in range(self.V):
            u = self.minDistance(dist, sptSet)
            sptSet[u] = True
            for v in range(self.V):
                if (self.graph[u][v] > 0 and
                sptSet[v] == False and
                dist[v] > dist[u] + self.graph[u][v]):
                    dist[v] = dist[u] + self.graph[u][v]
        list_of_distances = []
        for node in range(self.V):
            list_of_distances.append((node,dist[node]))
        print('k: ',k)
        return [x[0] for x in sorted(list_of_distances, key=lambda tup: tup[1])[1:k+1]]


    def matrix_graph(self, NODES, LINKS):
        with open(NODES) as json_file:
            data = json.load(json_file)
            json_nodes = data["nodes"]
            self.V = len(json_nodes)
        matrix_graph = [[0 for column in range(self.V)]
                          for row in range(self.V)]
        with open(LINKS) as json_file:
            data = json.load(json_file)
            json_links = data["links"]
            for item in json_links:
                link = item
                source_node = link["fromNode"]
                destination_node = link["toNode"]
                if source_node < destination_node:
                    matrix_graph[source_node][destination_node] = link["delay"]
                # ADD THIS CODE FOR T1 TOPOLOGY
                if self.hierarchical == False:
                    matrix_graph[destination_node][source_node] = link["delay"] 
        return matrix_graph 



def write_data(data, aggregation, latency, RU_latency, worsening_limit, data_file, k):
    sing_data = dict()
    sing_data['aggregation'] = aggregation
    sing_data['latency'] = latency
    sing_data['RU_latency'] = RU_latency
    data['worsening_limit_'+ str(worsening_limit) + k] = sing_data

    with open(data_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def read_data(data_file):
    try:
        with open(data_file, 'r') as json_file:
            d = json.load(json_file)
            print(len(d))
            return d
    except:
        print('cannot open file')
        return dict()

def data_generator(mdl, i, FO_Stage_0, worsening_limit, MEC_proc, MEC_load, rus, mec, paths, DRCs, crs, conj_Fs, data_file, k=''):    


    path_delay = sum(max((mdl.x[it].solution_value*(paths[it[0]].delay_p_mec + (paths[it[0]].delay_p2*min(1, paths[it[0]].seq[0])) + (paths[it[0]].delay_p3*min(1, paths[it[0]].seq[1])))for it in i if rus[it[2]].CR in mec and b==it[2])) for b in rus if rus[b].CR in mec)
    processing_delay = sum(max((mdl.x[it].solution_value*(((((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load)*0.25 + pow(((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load, 2)*0.25))for it in i if rus[it[2]].CR in mec and b==it[2])) for b in rus if rus[b].CR in mec)
    final_delay =  (path_delay + processing_delay)

    aggr = sum(sum(max(0, sum(min(1, sum(mdl.x[it].solution_value for it in i if (
                    (paths[it[0]].seq[0] == crs[c].id and it[2] == b and f in DRCs[it[1]].Fs_CU) or (
                        paths[it[0]].seq[1] == crs[c].id and it[2] == b and f in DRCs[it[1]].Fs_DU) or (
                                paths[it[0]].seq[2] == crs[c].id and it[2] == b and f in DRCs[it[1]].Fs_RU)))) for b in
                                                  rus) - 1) for f in conj_Fs) for c in crs)


    dict_rate = dict()
    for b in rus:
        if rus[b].CR in mec:
            dict_rate[b] = (max((mdl.x[it].solution_value*(paths[it[0]].delay_p_mec + (paths[it[0]].delay_p2*min(1, paths[it[0]].seq[0])) + (paths[it[0]].delay_p3*min(1, paths[it[0]].seq[1])))for it in i if rus[it[2]].CR in mec and b==it[2])) +
                                max((mdl.x[it].solution_value*(((((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load)*0.25 + pow(((MEC_proc)/(crs[paths[it[0]].mec_loc].cpu))*MEC_load, 2)*0.25))for it in i if rus[it[2]].CR in mec and b==it[2])))

    data = read_data(data_file)
    write_data(data, aggr, final_delay, dict_rate, worsening_limit, data_file, k)

    print("\n\n\nMEC_vRAN with flow split\n")
    print("#----------------------------------------#")
    print("inicial_delay:    | ", FO_Stage_0)
    print("worserning_limit: | ", worsening_limit)
    print("final delay:      | ", final_delay)
    print('path delay:       | ', path_delay)
    print('processing delay: | ', processing_delay)
    print('aggregation:      | ',aggr)
    print("#----------------------------------------#")

