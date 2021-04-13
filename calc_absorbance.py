#!/usr/local/bin/python3.7

'''
Calculates the absorbance time at a given absorbed percentage of the initial volume
for all tensiometer experiments in the database.
'''

import sys
import os
import sqlite3
from scipy import interpolate
from math import log
from math import exp
import matplotlib
import matplotlib.pyplot as plt
from colorhash import ColorHash
from exclude import exclusions

class Experiment():
    absorbance_time = -1

    def __init__(self, data, experiment, binder):
        age, ca_left, ca_avg, ca_right, height, bd, vol = 1, 2, 3, 4, 5, 6, 7
        initial_time = data[0][age]
        x = [ ((e[age] - initial_time)/1000)/experiment['fps'] for e in data ]
        y = [ e[vol] for e in data ] 
        self.x = x
        self.y = y
        self.binder = binder
        self.experiment = experiment
    
    def calc_absorbance_time(self, target_volume):
        #print(self.experiment['fps'], self.experiment['volume'], target_volume)
        target_volume = ((100 - target_volume)  / 100) * self.experiment['volume']
        pairs = [ (e[0], e[1]) for e in zip(self.x, self.y) if e[0] > 0 and e[1] > 0]
        x = [ log(e[0]) for e in pairs] # better extrapolation when time is on log scale
        y = [ e[1] for e in pairs]
        # Interpolation, if possible, else, extrapolation
        if (y[-1] > target_volume or y[0] < target_volume):
            print("Warning, extrapolating! Target is {}, max is {}, min is {}".format(target_volume, y[0], y[-1]), file=sys.stderr)
        interpolater = interpolate.interp1d(y, x, fill_value='extrapolate')
        abs_time = exp( interpolater(target_volume) ) # remember, x = log(time)
        #print("Absorbance time at given percentage is", abs_time, file=sys.stderr)
        self.absorbance_time = abs_time
        return abs_time

def plot(experiments):
    matplotlib.use("Agg")
    f = plt.figure()
    plt.yscale('linear')
    plt.xscale('linear')

    for e in experiments:
        plt.plot(e.x, [i/max(e.y) for i in e.y], color=ColorHash(e.binder_name).hex, label=e.binder_name)
        #plt.plot([exp(e) for e in x], [i/max(y) for i in y], color=ColorHash(binder_name).hex, label=binder_name)
    
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), fontsize='xx-small')
    f.savefig("plot.pdf", bbox_inches='tight')

def getExperiment(tens_exp_id, cursor):
    cursor.execute('''SELECT tens_exp_id, age, ca_left, ca_avg, ca_right, height,
                    bd, vol FROM tensiometer_data WHERE tensiometer_data.tens_exp_id = {};'''.format(tens_exp_id))
    data = cursor.fetchall()

    cursor.execute('SELECT * FROM tensiometer_experiments WHERE tens_exp_id = {};'.format(tens_exp_id))
    names = [description[0] for description in cursor.description]
    experiment_values = cursor.fetchone()
    experiment = {n:b for n,b in zip(names, experiment_values)}

    cursor.execute('SELECT * from binders WHERE binder_id = {};'.format(experiment['binder']))
    names = [description[0] for description in cursor.description]
    binder_values = cursor.fetchone()
    binder = {n:b for n,b in zip(names, binder_values)}

    print(data[0])
    return Experiment(data, experiment, binder)
    

def main():
    """
    Open the database file and calculate the absorbance time for all (new) experiments.
    """
    args = sys.argv
    if len(args) < 3:
        print('usage: calc-absorbance.py /path/to/data.db percent-absorbed')
        sys.exit(1)

    database_file = sys.argv[1]
    percent_absorbed = float(sys.argv[2])

    if os.path.exists(database_file):
        conn = sqlite3.connect(database_file)
        c = conn.cursor()
    else:
        print('Database file could not be found.')
        sys.exit(1)
    
    # Strategy:
    # - Get a list of all experiments
    # - For each experiment, get all the data points
    # - Then, calculate the absorbance time, and add it to a list
    # - Print the list
    
    results = []
    processed_experiments = []
    c.execute('''SELECT tens_exp_id, binder, binders.name, date, volume, fps, binders.per_conc,
               binders.viscosity, binders.surface_tension, binders.smooth_ca, binders.rough_ca, binders.cca_cos_theta, temperature
               FROM tensiometer_experiments LEFT JOIN binders on
               tensiometer_experiments.binder = binders.binder_id;''')
    for row in c:
        tens_exp_id, binder, binder_name, date, initial_volume, fps, concentration, viscosity, surface_tension, smooth_ca, rough_ca, cca_cos_theta, temperature = (row[0], row[1],
                    row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12])
        
        if tens_exp_id < 45 or tens_exp_id in exclusions():
            continue # new data only
        
        processed_experiment = getExperiment(tens_exp_id, conn.cursor())
        if processed_experiment.calc_absorbance_time(percent_absorbed) == 0:
            continue
        processed_experiments.append(processed_experiment)
        results.append([tens_exp_id, binder, binder_name, binder_name[0:3], concentration, date, processed_experiment.absorbance_time, initial_volume, viscosity, surface_tension, smooth_ca, rough_ca, cca_cos_theta, temperature])
    # Print the column headers, then the data entries
    print("tens_exp_id, binder_id, binder_name, binder_type, concentration, date, abs_time, initial_volume, viscosity, surface_tension, smooth_ca, rough_ca, cca_cos_theta, temperature")
    for r in results:
        print(' '.join([str(e) for e in r]))
    
    #plot(processed_experiments)
    

    if (percent_absorbed < 60):
        print("Warning: percent _absorbed_, not percent remaining!", file=sys.stderr)


# Main body
if __name__ == '__main__':
    main()