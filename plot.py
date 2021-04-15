#!/usr/local/bin/python3.7

"""
Autogenerate the plots for my thesis / article. With this module, I can quickly re-generate all the plots
when new data comes in. I can also standardize all the formatting.
"""

import numpy as np 
import matplotlib.pyplot as plt 
import sqlite3
import scipy.stats as stats
import calc_absorbance
from exclude import exclusions
from colorhash import ColorHash

def short_hash(string, debug=False):
    h = str(abs(hash(string)))[0:6]
    if debug:
        print(string)
        print(h)
    return h

def mainEffectsPlot(data=None, xlevels=[], sublevels=[], xlabels=None, log=False, ylabel=None, sublevels_labels=None, colours=['#b36c48', '#afb59b', '#816853'], boxes=True):
    """
    Create a main effects plot for x levels and s sublevels. The sublevels and xlevels lists are lists of
    lists -- the entries within each represent all the possible options for that sublevel / xlevel.
    """
    # https://stackoverflow.com/questions/16592222/matplotlib-group-boxplots

    def set_box_color(bp, color):
        #plt.setp(bp['boxes'], color=color)
        #plt.setp(bp['whiskers'], color=color)
        #plt.setp(bp['caps'], color=color)
        plt.setp(bp['medians'], color=color)

    plt.figure()

    inter_xlevel_spacing = 1
    inter_sublevel_spacing = 0.30

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
    i = 0
    xs = []; ys = []; dof = []; stdev = [] # if not making a box plot
    for x in xlevels:
        i += inter_xlevel_spacing
        c = 0
        for s in sublevels:
            index = short_hash(str(x)+str(s))
            if boxes:
                b = plt.boxplot(series[index], positions=[i], showfliers=False, notch=True) # don't show outliers, since we include a scatter plot
                set_box_color(b, colours[c])
                plt.scatter(np.random.normal( i, 0.04, len(series[index]) ), series[index], c=colours[c], alpha=0.75 )
            else:
                xs.append(i)
                ys.append( sum(series[index]) / len(series[index]) )
                dof.append( len(series[index]) - 1 )
                stdev.append( np.std(series[index]) )
                plt.plot(i, sum(series[index])/len(series[index]), marker='o', c=colours[c])
            i+= inter_sublevel_spacing
            c += 1

    # plot t-test error bars if not doing box plots
    if not boxes:
        stdev=np.array(stdev); dof=np.array(dof)
        plt.errorbar(xs, ys, yerr=stats.t.ppf(0.95, dof)*stdev, fmt='none', ecolor='#000000', capsize=3)

        # add lines between the levels
        trendlines = [ [] for i in xlevels ]
        k = 0
        for i,x in enumerate(xlevels):
            k += inter_xlevel_spacing
            for j,s in enumerate(sublevels):
                index = short_hash(str(x)+str(s))
                trendlines[j].append( (k, sum(series[index])/len(series[index]), series[index]) )
                k += inter_sublevel_spacing
        c = 0
        for t in trendlines:
            plt.plot([p[0] for p in t], [p[1] for p in t], linewidth=1, c=colours[c])
            if len(t) == 2:
                ttest = stats.ttest_rel(t[0][2], t[1][2], alternative='two-sided')[1]
                if ttest < 0.001:
                    ttest_text = '{:0.1e}'.format(ttest)
                else:
                    ttest_text = '{:.3f}'.format(ttest)
                x_position = (t[1][0] - t[0][0])/2 + t[0][0]
                y_position = (t[1][1] - t[0][1])/2 + t[0][1] + (plt.ylim()[1] - plt.ylim()[0]) * 0.1
                plt.text( x_position, y_position, "p = "+ttest_text, style='italic', color=colours[c], horizontalalignment='center')
            c += 1


    # add the labels on the x-axis
    if xlabels != None:
        ticks = []
        ticks.append( inter_xlevel_spacing + (len(sublevels) - 1)*inter_sublevel_spacing/2 )
        for i in range(len(xlevels[1:])):
            ticks.append( (len(ticks)+1)*inter_xlevel_spacing + len(sublevels)*inter_sublevel_spacing + (len(sublevels) - 1)*inter_sublevel_spacing/2 )
        plt.xticks(ticks, xlabels)
    else:
        plt.xticks = None
    
    if ylabel != None:
        plt.ylabel(ylabel)

    if log:
        plt.yscale("log")

    if sublevels_labels:
        c = 0
        for s in sublevels_labels:
            plt.plot([], c=colours[c], label=s)
            c += 1
        plt.legend()


    plt.show()
    return


def doeMeanPlot(data, levels, names, ylabel=None, log=False):
    """
    Levels is a list of lists of lists, each inner list contains the levels to split by.
    e.g. levels = [ [[x-low], [x-high]], [[y-low], [y-high]] ]
    """
    series = {}
    for d in data:
        for l in levels:
                for ll in l:
                    index = short_hash(str(l)+str(ll))
                    for lll in ll:
                        if not lll in d.binder['name']:
                            continue
                        if index in series:
                            series[index].append(d.absorbance_time)
                        else:
                            series[index] = [d.absorbance_time]

    # add points to the figure
    i = 0.25
    x = []
    y = []
    dof = []
    stdev = []
    for l in levels:
        for ll in l:
            index = short_hash(str(l)+str(ll))
            x.append(i)
            y.append( sum(series[index])/len(series[index]) )
            dof.append( len(series[index]) - 1 )
            stdev.append( np.std(series[index]) )
            i += 0.5
    plt.scatter(x, y, c='#000000')
    for i in range(0, len(y), 2):
        plt.plot([x[i], x[i+1]], [y[i], y[i+1]], linewidth=1, c='#000000')
    
    # https://stackoverflow.com/questions/20033396/how-to-visualize-95-confidence-interval-in-matplotlib
    stdev=np.array(stdev)   #(Standard Deviations of your data)
    dof=np.array(dof)
    plt.errorbar(x, y, yerr=stats.t.ppf(0.95, dof)*stdev, fmt='none', ecolor='#000000', capsize=3)

    ticks = [0.5 + n for n,i in enumerate(levels)]
    plt.xticks(ticks, names)

    if log:
        plt.yscale("log")
    else:
        plt.ylim(bottom=0)

    if ylabel:
        plt.ylabel(ylabel)

    plt.show()


def plotAbsorptionProfiles(experiments, id=False, log=False):
    plt.yscale('linear')
    if log:
        plt.xscale('log')
    else:
        plt.xscale('linear')

    for e in experiments:
        if id:
            plt.plot(e.x, [i/max(e.y) for i in e.y], color=ColorHash(e.experiment['tens_exp_id']).hex, label=e.experiment['tens_exp_id'])
        else:
            plt.plot(e.x, [i/max(e.y) for i in e.y], color=ColorHash(e.binder['name']).hex, label=e.binder['name'])
    
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), fontsize='small')
    plt.ylabel("Fraction of pre-impact volume")
    plt.xlabel("Absorption time (s)")
    plt.show()

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

    # useful for checking a particular binder
    #plotAbsorptionProfiles([e for e in experiments if 'pvp-360k-low-u-high' in e.binder['name']], id=True, log=True)
    
    # Global view of all data
    #plotAbsorptionProfiles(experiments, log=True)
    #plotAbsorptionProfiles(experiments)

    # Colours, via https://artsexperiments.withgoogle.com/artpalette/
    pvp_40_360_colours = ['#b36c48', '#afb59b', '#816853']
    single_colour = ['#000000', '#000000', '#000000']
    lh_mw_colours = ['#454d7d', '#594540', '#c6b165']
    species_colours = ['#314435', '#9a3c34', '#455266']

    # PVP-only data
    
    pvp_only = [e for e in experiments if 'pvp' in e.binder['name']]

    #doeMeanPlot(pvp_only, [[['low-u'], ['high-u']], [['low-y'], ['high-y']], [['40k'], ['360k']]], ['μ', 'γ', 'MW'], ylabel="Absorption time (s)")
    
    mainEffectsPlot(pvp_only, [['low-u'], ['high-u']], [['40k'], ['360k']], xlabels=['Low μ', 'High μ'],
        log=False, ylabel="Absorption time (s)", sublevels_labels=["PVP 40k", "PVP 360k"], colours=pvp_40_360_colours, boxes=False)
    mainEffectsPlot(pvp_only, [['low-u'], ['high-u']], [['40k'], ['360k']], xlabels=['Low μ', 'High μ'],
        log=False, ylabel="Absorption time (s)", sublevels_labels=["PVP 40k", "PVP 360k"], colours=pvp_40_360_colours, boxes=True)
    
    mainEffectsPlot(pvp_only, [['low-y'], ['high-y']], [['40k'], ['360k']], xlabels=['Low γ', 'High γ'],
        log=False, ylabel="Absorption time (s)", sublevels_labels=["PVP 40k", "PVP 360k"], colours=pvp_40_360_colours, boxes=False)
    mainEffectsPlot(pvp_only, [['low-y'], ['high-y']], [['40k'], ['360k']], xlabels=['Low γ', 'High γ'],
        log=False, ylabel="Absorption time (s)", sublevels_labels=["PVP 40k", "PVP 360k"], colours=pvp_40_360_colours, boxes=True)
    
    mainEffectsPlot(pvp_only, [['40k'], ['360k']], [['pvp']], xlabels=['PVP 40k', 'PVP 360k'],
        ylabel="Absorption time (s)", colours=single_colour, boxes=False)
    mainEffectsPlot(pvp_only, [['40k'], ['360k']], [['pvp']], xlabels=['PVP 40k', 'PVP 360k'],
        ylabel="Absorption time (s)", colours=single_colour, boxes=True)
    
    # Low-y only data
    all_binders = [e for e in experiments if 'low-y' in e.binder['name']]

    doeMeanPlot(all_binders, [[['low-u'], ['high-u']], [['10k', '40k'], ['124k', '360k']], [['pva'], ['pvp']]], ['μ', 'MW', 'PVA, PVP'], ylabel="Absorption time (s)")

    mainEffectsPlot(all_binders, [['low-u'], ['high-u']], [['10k', '40k'], ['124k', '360k']],
        xlabels=['Low μ', 'High μ'], log=False, ylabel="Absorption time (s)", sublevels_labels=["Low MW", "High MW"], colours=lh_mw_colours, boxes=False)
    mainEffectsPlot(all_binders, [['low-u'], ['high-u']], [['10k', '40k'], ['124k', '360k']],
        xlabels=['Low μ', 'High μ'], log=False, ylabel="Absorption time (s)", sublevels_labels=["Low MW", "High MW"], colours=lh_mw_colours, boxes=True)

    mainEffectsPlot(all_binders, [['10k', '40k'], ['124k', '360k']], [['pva'], ['pvp']], xlabels=['Low MW', 'High MW'],
        log=False, ylabel="Absorption time (s)", sublevels_labels=["PVA", "PVP"], colours=species_colours, boxes=False)
    mainEffectsPlot(all_binders, [['10k', '40k'], ['124k', '360k']], [['pva'], ['pvp']], xlabels=['Low MW', 'High MW'],
        log=False, ylabel="Absorption time (s)", sublevels_labels=["PVA", "PVP"], colours=species_colours, boxes=True)
        
    mainEffectsPlot(all_binders, [['pva'], ['pvp']], [['low-y']], xlabels=['PVA', 'PVP'], ylabel="Absorption time (s)", colours=single_colour, boxes=False)
    mainEffectsPlot(all_binders, [['pva'], ['pvp']], [['low-y']], xlabels=['PVA', 'PVP'], ylabel="Absorption time (s)", colours=single_colour, boxes=True)

if __name__ == '__main__':
    main()