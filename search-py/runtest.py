#!/usr/bin/env python
from common import init_base
from functools import partial
import os
import sys
import getopt

def run_with_graph(func):
    from pycallgraph import PyCallGraph
    from pycallgraph.output import GraphvizOutput
    output = GraphvizOutput()
    output.output_file = 'callgraph.png'
    with PyCallGraph(output=GraphvizOutput()):
        func()

def run_with_profile(func):
    import cProfile, pstats, StringIO
    pr = cProfile.Profile(builtins = False)
    #pr.enable()
    try:
        #func()
        pr.runcall(func = func)
    finally:
        #pr.disable()
        s = StringIO.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats('/base.*py:')
        print s.getvalue()
        ps.dump_stats('profile.dat')

def build_test():
    import unittest
    suite  = unittest.defaultTestLoader.discover(        \
            start_dir = 'tests', pattern = 'test_*.py')
    runner = unittest.TextTestRunner()
    unittest.TestCase.longMessage = True
    return (runner, suite)

def main(argv = sys.argv[1:]):
    # parse command line options
    init_base()
    try:
        opts, args = getopt.getopt(argv, 'gpv', ['graph', 'profile', 'verbose'])
    except getopt.error, msg:
        print msg
        sys.exit(2)
    (runner, suite) = build_test()
    main_func = partial(runner.run, suite)

    # process options
    for o, a in opts:
        if o in ('-g', '--graph'):
            main_func = partial(run_with_graph, main_func)
        elif o in ('-p', '--profile'):
            main_func = partial(run_with_profile, main_func)
        elif o in ('-v', '--verbose'):
            runner.verbosity = 2
    main_func()

if __name__ == '__main__':
    main()
