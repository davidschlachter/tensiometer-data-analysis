#!/usr/local/bin/python3.7
"""
Module to exclude 'bad' experimental runs. Mostly repeated runs where the previous set of data used a bad tip size.
"""

import os

def exclusions():
    f = "excludes.txt"
    e = []
    if os.path.exists(f):
        e = [ int(l.strip()) for l in open(f).readlines()]
    return e