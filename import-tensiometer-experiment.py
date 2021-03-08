#!/usr/local/bin/python3.7
"""
Import a text-file describing a tensiometer experiment into my sqlite database for experiments
"""

import sys
import os
import sqlite3
import csv


def main():
    args = sys.argv

    if len(args) < 7:
        print('usage: import-tensiometer-experiment.py /path/to/data.db /path/to/experiment.txt binderid "ISO-8601 date" initialDropVolume[ul] fps')
        sys.exit(1)
    
    databaseFile = sys.argv[1]
    experimentFile = sys.argv[2]
    binderID = sys.argv[3]
    exptDate = sys.argv[4]
    dropVol = sys.argv[5]
    fps = sys.argv[6]

    if os.path.exists(databaseFile):
        conn = sqlite3.connect(databaseFile)
        c = conn.cursor()
    else:
        print('Database file could not be found.')
        sys.exit(1)
    
    if not os.path.exists(experimentFile):
        print('Experiment file not found.')
        sys.exit(1)

    # Go ahead an create the experiment. Assume that the date is well-formatted, do check that the binderid exists though
    c.execute("SELECT 1 FROM binders WHERE binder_id=?;", [binderID])
    if not c.fetchone():
        print("binderid could not be found in database")
        sys.exit(1)

    c.execute("INSERT into tensiometer_experiments (binder,date,volume,fps) values (?, ?, ?, ?);", (binderID, exptDate, dropVol, fps))
    experimentID = c.lastrowid

    # Now the tricky part, inseert the data that corresponds to the experiment
    with open(experimentFile) as csvfile:
        csvreader = csv.reader(csvfile, delimiter='\t')
        next(csvreader) # all the files have a header row
        for row in csvreader:
            c.execute("INSERT into tensiometer_data (tens_exp_id, run_no, age, ca_left, ca_avg, ca_right, ift, ift_err, height, bd, vol) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (experimentID, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
    
    conn.commit()
    


    



# Main body
if __name__ == '__main__':
    main()