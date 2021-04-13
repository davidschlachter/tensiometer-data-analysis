#!/usr/local/bin/python3.7

"""
Autogenerate the plots for my thesis / article. With this module, I can quickly re-generate all the plots
when new data comes in. I can also standardize all the formatting.
"""

import numpy as np 
import matplotlib.pyplot as plt 
import sqlite3
import calc_absorbance
from exclude import exclusions

def short_hash(string, debug=False):
    h = str(abs(hash(string)))[0:6]
    if debug:
        print(string)
        print(h)
    return h


def main_effects_plot(data=None, xlevels=[], sublevels=[], xlabels=None, log=False, ylabel=None):
    """
    Create a main effects plot for x levels and s sublevels. The sublevels and xlevels lists are lists of
    lists -- the entries within each represent all the possible options for that sublevel / xlevel.
    """
    # https://stackoverflow.com/questions/16592222/matplotlib-group-boxplots

    def set_box_color(bp, color):
        plt.setp(bp['boxes'], color=color)
        plt.setp(bp['whiskers'], color=color)
        plt.setp(bp['caps'], color=color)
        plt.setp(bp['medians'], color=color)

    plt.figure()

    # separate out the data series
    # this started elegant, got messy fast. refactor later.
    series = {}
    for d in data:
        for x in xlevels:
            for xx in x:
                for s in sublevels:
                    index = short_hash(str(x)+str(s))
                    for ss in s:
                        if not ss in d.binder['name'] or not xx in d.binder['name']:
                            continue
                        if index in series:
                            series[index].append(d.absorbance_time)
                        else:
                            series[index] = [d.absorbance_time]
    
    # add the box plots and the scatter dots to the figure
    i = 1
    for x in xlevels:
        for s in sublevels:
            index = short_hash(str(x)+str(s), debug=True)
            plt.boxplot(series[index], positions=[i])
            plt.scatter(np.random.normal( i, 0.04, len(series[index]) ), series[index], c='#D7191C', alpha=0.4  )
            i+= 1

    # add lines between the levels
    trendlines = [ [] for i in xlevels ]
    k = 1
    for i,x in enumerate(xlevels):
        for j,s in enumerate(sublevels):
            index = short_hash(str(x)+str(s))
            trendlines[j].append( (k, sum(series[index])/len(series[index])) )
            k += 1
    for t in trendlines:
        plt.plot([p[0] for p in t], [p[1] for p in t], linewidth=1)


    # add the labels on the x-axis
    if xlabels != None:
        ticks = []
        ticks.append(( ((len(xlevels)*len(sublevels)//2)-1) * 0.5) + 1)
        for i in range(len(xlevels[1:])):
            ticks.append( ticks[-1:][0] + len(sublevels) )
        plt.xticks(ticks, xlabels)
    else:
        plot.xticks = None

    if ylabel != None:
        plt.ylabel(ylabel)

    if log:
        plt.yscale("log")

    plt.show()
    return

    # Old code, maybe get into above
    set_box_color(bpl1, '#D7191C')
    set_box_color(bpl2, '#2C7BB6')
    set_box_color(bpr1, '#D7191C')
    set_box_color(bpr2, '#2C7BB6')
    # draw temporary red and blue lines and use them to create a legend
    #plt.plot([], c='#D7191C', label='PVP 40k')
    #plt.plot([], c='#2C7BB6', label='PVP 360k')
    #plt.legend()
    #plt.yscale("log")
    

    fig = plt.gcf()
    fig.set_size_inches(3.1496, 2.3622, forward=True)
    plt.show()
    fig.savefig('../new-dataanalysis/pvp-only-viscosity.png', dpi=300)



def main():
    conn = sqlite3.connect("/usr/home/zbox/syncthing/Synced/2021-maitrise/in-progress/data.sqlite")
    c = conn.cursor()

    experiments = []

    c.execute('''SELECT tens_exp_id, binder, binders.name, date, volume, fps, binders.per_conc,
                binders.viscosity, binders.surface_tension, binders.smooth_ca, binders.rough_ca,
                binders.cca_cos_theta, temperature FROM tensiometer_experiments LEFT JOIN binders on
                tensiometer_experiments.binder = binders.binder_id;''')

    # get all the experiments for 'low-high' binders, room-temperature only, droplet size in-spec
    for row in c.fetchall():
        if not ('-low' in row[2] or '-high' in row[2]) or row[12] > 30:
            continue
        if row[0] in exclusions(): # skip 'known-bad' exp_id's -- repeated experiments with better tip size particularly
            continue
        #print(row)
        e = calc_absorbance.getExperiment(row[0], conn.cursor())
        e.calc_absorbance_time(79) # hard-coded for the moment
        experiments.append(e)

    # PVP-only data
    pvp_only = [e for e in experiments if 'pvp' in e.binder['name']]
    for e in [e.experiment['tens_exp_id'] for e in pvp_only]:
        print(e)
    main_effects_plot(pvp_only, [['low-u'], ['high-u']], [['40k'], ['360k']], xlabels=['Low μ', 'High μ'], log=False, ylabel="Absorption time (s)")
    main_effects_plot(pvp_only, [['low-y'], ['high-y']], [['40k'], ['360k']], xlabels=['Low γ', 'High γ'], log=False, ylabel="Absorption time (s)")
    main_effects_plot(pvp_only, [['40k'], ['360k']], [['pvp']], xlabels=['PVP 40k', 'PVP 360k'], ylabel="Absorption time (s)")

    # Low-y only data
    all_binders = [e for e in experiments if 'low-y' in e.binder['name']]
    main_effects_plot(all_binders, [['low-u'], ['high-u']], [['10k', '40k'], ['124k', '360k']], xlabels=['Low μ', 'High μ'], log=False, ylabel="Absorption time (s)")
    main_effects_plot(all_binders, [['10k', '40k'], ['124k', '360k']], [['pva'], ['pvp']], xlabels=['Low MW', 'High MW'], log=False, ylabel="Absorption time (s)")
    main_effects_plot(all_binders, [['pva'], ['pvp']], [['low-y']], xlabels=['PVA', 'PVP'], ylabel="Absorption time (s)")

if __name__ == '__main__':
    main()