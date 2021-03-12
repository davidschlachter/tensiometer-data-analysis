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

def calcAbsorbance(binder, experiment, percent_absorbed):
    tens_exp_id, binder, binder_name, date, initial_volume, fps = (binder[0], binder[1],
                    binder[2], binder[3], binder[4], binder[5])
    print(binder, file=sys.stderr)
    if len(experiment) == 0:
        print("Warning: experiment has no entries", file=sys.stderr)
        return 0
    print(experiment[0], file=sys.stderr)
    # The column indices
    age, ca_left, ca_avg, ca_right, height, bd, vol = 1, 2, 3, 4, 5, 6, 7
    # Find the time corresponding to the target volume
    target_volume = ((100 - percent_absorbed)  / 100) * initial_volume
    # frame times in the files are just the frame number * 1000 when imported
    # from AVI files.
    initial_time = experiment[0][age]
    x = [ ((e[age] - initial_time)/1000)/fps for e in experiment ]
    y = [ e[vol] for e in experiment ]
    # note that this throws away the first data point (t == 0)
    pairs = [ (e[0], e[1]) for e in zip(x, y) if e[0] > 0 and e[1] > 0]
    x = [ log(e[0]) for e in pairs] # better extrapolation when time is on log scale
    y = [ e[1] for e in pairs]
    # Interpolation, if possible, else, extrapolation
    if (experiment[-1][vol] > target_volume or experiment[0][vol] < target_volume):
        print("Warning, extrapolating! Target is {}, max is {}, min is {}".format(target_volume, experiment[0][vol], experiment[-1][vol]), file=sys.stderr)
    interpolater = interpolate.interp1d(y, x, fill_value='extrapolate')
    abs_time = exp( interpolater(target_volume) ) # remember, x = log(time)
    print("Absorbance time at given percentage is", abs_time, file=sys.stderr)
    return abs_time

def main():
    args = sys.argv
    if len(args) < 3:
        print('usage: calc-absorbance.py /path/to/data.db percent-absorbed')
        sys.exit(1)

    database_file = sys.argv[1]
    percent_absorbed = float(sys.argv[2])

    if os.path.exists(database_file):
        conn = sqlite3.connect(database_file)
        c = conn.cursor()
        d = conn.cursor()
    else:
        print('Database file could not be found.')
        sys.exit(1)
    
    # Strategy:
    # - Get a list of all experiments
    # - For each experiment, get all the data points
    # - Then, calculate the absorbance time, and add it to a list
    # - Print the list
    # Caveats: there will be n+1 database queries
    results = []
    c.execute('''SELECT tens_exp_id, binder, binders.name, date, volume, fps, binders.per_conc
               FROM tensiometer_experiments LEFT JOIN binders on
               tensiometer_experiments.binder = binders.binder_id;''') 
    for row in c:
        tens_exp_id, binder, binder_name, date, initial_volume, fps, concentration = (row[0], row[1],
                    row[2], row[3], row[4], row[5], row[6])
        d.execute('''SELECT tens_exp_id, age, ca_left, ca_avg, ca_right, height,
                    bd, vol FROM tensiometer_data
                    WHERE tens_exp_id = {};'''.format(tens_exp_id)) 
        experiment = d.fetchall()
        abs_time = calcAbsorbance(row, experiment, percent_absorbed)
        if abs_time == 0:
            continue
        results.append([tens_exp_id, binder,    binder_name, binder_name[0:3], concentration, date, abs_time, initial_volume])
    # Print the column headers, then the data entries
    print(             "tens_exp_id, binder_id, binder_name, binder_type,      concentration, date, abs_time, initial_volume")
    for r in results:
        print(' '.join([str(e) for e in r]))


# Main body
if __name__ == '__main__':
    main()