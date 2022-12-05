import matplotlib.pyplot as plt
import json

data_file_model = 'complete_model_dados.json'
data_file_res_drc_fix_cu = 'rest_drc_fix_cu_dados.json'

fig, (ax,ax2) = plt.subplots(2, sharex=True)
fig.subplots_adjust(right=0.75)

fig.set_size_inches(10, 4.5)

dist = [32,48,64,96,128,192,256]
dist2 = [32,48,64]

aggr1 = [50, 78, 104]
aggr2 = [50, 78, 104, 170, 230, 311, 435]
aggr3 = [14, 14, 14, 30, 30, 30, 30]

time1 = [204, 5668, 52748]
time2 = [240, 3600, 4500, 10200, 15300, 37200, 66900]
time3 = [53, 242, 232, 1040, 1976, 5109, 10437]


#Agregation plot
##################################
p1, = ax.plot(dist2, aggr1, "-s", label="Complete model", linewidth=2.0, markersize=12, color='#006bb3')
p2, = ax.plot(dist, aggr2, "-.^",label="Heuristic Model", linewidth=2.0, markersize=12, color='#ff9900')
p3, = ax.plot(dist, aggr3, "r-.v",label="Fixed CU Restricted DRCs", linewidth=2.0, markersize=12)
ax.set_ylabel("Centralization", fontsize=16, labelpad=28)
ax.set_xticks([0,32,48,64,96,128,192,256])
ax.set_xticklabels([], fontsize=16)
ax.set_yticks([0,100,200,300,400])
ax.set_yticklabels([0,100,200,300,400], fontsize=16)
tkw = dict(size=4, width=1.5)
ax.tick_params(axis='y', **tkw, labelsize=16)
ax.tick_params(axis='x', **tkw, labelsize=16)
##################################



pc, = ax.plot([], [], "-s",label="Optimal model *", color='#006bb3')
ph, = ax.plot([], [], "-.^",label="Heuristic model", color='#ff9900')
pr, = ax.plot([], [], "r-.v",label="RVFC")
a = ax.legend(handles=[pc, ph, pr], fontsize=12, bbox_to_anchor=(0.92, 1.25),  ncol=3, frameon=False)
ax.add_artist(a)



#Time plot
##################################
ax2.plot(dist2, time1, "-s", label="Complete model", linewidth=2.0, markersize=12, color='#006bb3')
ax2.plot(dist, time2, "-.^",label="Heuristic Model", linewidth=2.0, markersize=12, color='#ff9900')
ax2.plot(dist, time3, "r-.v",label="Fixed CU Restricted DRCs", linewidth=2.0, markersize=12)
ax2.set_ylabel("Solution time (s)", fontsize=16, labelpad=8)
ax2.set_xlabel("Number of nodes",fontsize=16)
tkw = dict(size=4, width=1.5)
ax2.tick_params(axis='y', **tkw, labelsize=16)
ax2.tick_params(axis='x', **tkw, labelsize=16)
ax2.set_xticks([0,32,48,64,96,128,192,256])
ax2.set_xticklabels([0,32,48,64,96,128,192,256], fontsize=16)
ax2.set_yticks([3600,21600,43200,64800,86400])
ax2.set_yticklabels([3600,21600,43200,64800,86400], fontsize=16)
###################################

ax.grid(True, axis='y', linestyle='--')
ax2.grid(True, axis='y', linestyle='--')
plt.savefig("cr_aggr_time.pdf", bbox_inches='tight')
plt.show()