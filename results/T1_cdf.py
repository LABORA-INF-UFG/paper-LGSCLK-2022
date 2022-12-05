import numpy as np
#from pylab import *
import matplotlib.pyplot as plt
import json

data_file_model = 't1_complete_model_dados.json'
data_file_res_drc_fix_cu = 't1_rest_drc_fix_cu_dados.json'

with open(data_file_model, 'r') as json_file:
    data = json.load(json_file)
cm = data

with open(data_file_res_drc_fix_cu, 'r') as json_file:
    data = json.load(json_file)
rdfc = data

#values = list(map(float, ['%.1f' % elem for elem in list(np.linspace(0.1,10,100))]))

#print(values)

def create_data(list_values):
    values = list(map(float, ['%.1f' % elem for elem in list(np.linspace(0.1,9.0,100))]))
    count =  [0]*100
    #print(values)
    for item in list_values:
        func_lamb = lambda x: x+1 if (list_values[item] < values[i]) else x
        for i in range(0,len(values)):
            count[i] = func_lamb(count[i])

    for i in range(0,len(values)):
        count[i] = count[i]/len(list_values)

    return (values, count)


fig, ax = plt.subplots()
fig.set_size_inches(10, 3.5)

ax.set_xlabel('BS latency (ms)', fontsize=20)
ax.set_ylabel('Occurrence (%)', fontsize=20)

pa, = ax.plot([], [], "-",label="WL=1ms", color='#cc0000')
pb, = ax.plot([], [], "-",label="WL=2ms", color='#990000')
pc, = ax.plot([], [], "-",label="WL=3ms", color='#999900')
pd, = ax.plot([], [], "-",label="WL=4ms", color='#009900')
pe, = ax.plot([], [], "-",label="WL=5ms", color='#009999')
pf, = ax.plot([], [], "-",label="WL=6ms", color='#002699')
pg, = ax.plot([], [], "-",label="WL=7ms", color='#9900cc')
ph, = ax.plot([], [], "-",label="WL=8ms", color='#ff00bf')
pi, = ax.plot([], [], "-",label="WL=9ms", color='#ff0000')
ax.legend(handles=[pb, pe, pg, pi], fontsize=14, loc='lower right')

#values, count= create_data(cm['worsening_limit_1']['RU_latency'])
#ax.plot(values, count, "r-",label="Rest. drc fixed cu", linewidth=2, color='#cc3300')

#values, count= create_data(cm['worsening_limit_1.0']['RU_latency'])
#p = ax.plot(values, count, "r-",label="Rest. drc fixed cu", linewidth=2, color='#cc0000')

values, count= create_data(cm['worsening_limit_2.0']['RU_latency'])
p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#990000')

#values, count= create_data(cm['worsening_limit_3.0']['RU_latency'])
#p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#999900')

#values, count= create_data(cm['worsening_limit_4.0']['RU_latency'])
#p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#009900')

values, count= create_data(cm['worsening_limit_5.0']['RU_latency'])
p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#009999')

#values, count= create_data(cm['worsening_limit_6.0']['RU_latency'])
#p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#002699')

values, count= create_data(cm['worsening_limit_7.0']['RU_latency'])
p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#9900cc')

#values, count= create_data(cm['worsening_limit_8.0']['RU_latency'])
#p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#ff00bf')

values, count= create_data(cm['worsening_limit_9.0']['RU_latency'])
p = ax.plot(values, count, "-",label="Rest. drc fixed cu", linewidth=2, color='#ff0000')

tkw = dict(size=4, width=1.5)
ax.tick_params(axis='y', **tkw, labelsize=20)

ax.tick_params(axis='x', **tkw, labelsize=20)

ax.set_xticks([0,1,2,3,4,5,6,7,8,9])
ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

ax.grid(b=True, which='major', linestyle='--')

plt.savefig("T1_cdf.pdf", bbox_inches='tight')
plt.show()