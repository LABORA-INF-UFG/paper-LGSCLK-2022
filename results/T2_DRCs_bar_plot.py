import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
num_rus = 30

def plot_dsg_number():
    x = ['Optimal', 'RVFC']
    colors_list = ["", "darkgoldenrod", "gold", "black", "midnightblue", "blue", "royalblue", "cornflowerblue", "darkgray", "lightgray", "firebrick"]

    y = {}

    y[5] = [0, 0]                                        # DRC 1 - 1                                             
    y[4] = [0, 0]                                        # DRC 2 - 2                                             
    y[7] = [0, 0]                                        # DRC 4 - 7                                             
    y[6] = [0, 0]                                        # DSG 5 - 8                                             
    y[9] = [0, 0]                                        # DSG 6 - 12                                
    y[8] = [27/num_rus*100, 8/num_rus*100]               # DSG 7 - 13                               
    y[10] = [3/num_rus*100, 22/num_rus*100]              # DSG 8 - DRAN   
    y[1] = [0, 0]                                        # DSG 9 - 18 - CRAN                         
    y[2] = [0, 0]                                        # DSG 10 - 17 - CRAN                        

    peso = [0, 1, 4, 0, 5, 6, 7, 8, 9, 10, 25]

    for count in range(0, 2):
        sum_peso = 0
        for i in y:
            list = y[i]
            sum_peso += list[count]*peso[i]

        print(sum_peso)

    prev = {}

    for i in [1, 2, 4, 5, 6, 7, 8, 9, 10]:
        if i == 1:
            prev[1] = [0, 0]
        else:
            aux_prev = prev[ant]
            aux_y = y[ant]
            new = []
            for c in range(0, len(aux_prev)):
                new.append(aux_prev[c] + aux_y[c])
            prev[i] = new
        ant = i

    fig, ax = plt.subplots(figsize=(7, 3))

    plt.ylim(0, 105)
    plt.xlim(-0.5, 1.5)

    plt.yticks([0, 25, 50, 75, 100])

    for i in y:
        ax.bar(x, y[i], width=.7, color=colors_list[i], bottom=prev[i])

    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(16)

    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(18)

    ax.set_ylabel('VNCs (%)', fontsize=30)

    ax.tick_params(axis='y', which='major', labelsize=30)
    ax.tick_params(axis='x', which='major', labelsize=30)


    pa, = ax.plot([], [], "-",label="NG-RAN (2)", color='darkgray', linewidth=8.0)
    pb, = ax.plot([], [], "-",label="D-RAN", color='firebrick', linewidth=8.0)
    ax.legend(handles=[pa, pb], fontsize=24, bbox_to_anchor=(1.05, 1.3),  ncol=3, frameon=False, columnspacing=1)


    #legend_elements = [Line2D([0], [0], color='b', lw=4, label='NG-RAN (3)'),
    #                   Line2D([0], [0], color='gray', lw=4, label='NG-RAN (2)'),
    #                   Line2D([0], [0], color='darkgoldenrod', lw=4, label='C-RAN'),
    #                   Line2D([0], [0], color='brown', lw=4, label='D-RAN')]
    
    #ax.legend(handles=legend_elements, loc="lower right")
    ax.yaxis.grid(color='gray', linestyle='--', linewidth=0.5)

    plt.savefig("DRCs_T2.pdf", bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    plot_dsg_number()