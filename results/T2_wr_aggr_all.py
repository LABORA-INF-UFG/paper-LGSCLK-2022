import matplotlib.pyplot as plt
import json

data_file_model = 'complete_model_dados.json'
data_file_res_drc_fix_cu = 'rest_drc_fix_cu_dados.json'

fig, ax = plt.subplots()
fig.subplots_adjust(right=0.75)

fig.set_size_inches(6, 4)

dist = [0.5, 1, 1.5, 2, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]

with open(data_file_model, 'r') as json_file:
    data = json.load(json_file)

aggreg1 = [data[x]['aggregation'] for x in data]


with open(data_file_res_drc_fix_cu, 'r') as json_file:
    data = json.load(json_file)
    
aggreg2 = [data[x]['aggregation'] for x in data]


p1, = ax.plot(dist, aggreg1, "b-s", label="Complete model", linewidth=2.0)
p3, = ax.plot(dist, aggreg2, "y-s",label="Fixed CU Restricted DRCs", linewidth=2.0)


pc, = ax.plot([], [], "bs",label="Optimal model")
pr, = ax.plot([], [], "ys",label="RVFC")


ax.set_xlabel("Worsening limit (ms)",fontsize=20)
ax.set_ylabel("Centralization", fontsize=20)

ax.set_xticks([0,1,2,3,4,5, 6, 7])
ax.set_xticklabels([0,1,2,3,4,5, 6, 7], fontsize=20)

ax.set_yticks([0,10,20,30,40,50])
ax.set_yticklabels([0,10,20,30,40,50], fontsize=20)

tkw = dict(size=4, width=1.5)
ax.tick_params(axis='y', **tkw, labelsize=20)


ax.tick_params(axis='x', **tkw, labelsize=20)

a = ax.legend(handles=[pc, pr], fontsize=16, bbox_to_anchor=(1, 1.15),  ncol=3, frameon=False, columnspacing=1, handletextpad=0.1)
ax.add_artist(a)

plt.grid(True, linestyle=':')

plt.savefig("T2_aggregation_wl.pdf", bbox_inches='tight')
plt.show()