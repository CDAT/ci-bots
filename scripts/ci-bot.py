#!/usr/bin/env python
import argparse
import threading
import cibot
import json
import sys
import time

parser = argparse.ArgumentParser(description='Listens for requested CI',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "-f",
    "--frequency",
    help="Frequency at which to check for new ommits to test",
    type=int,
    default=5)
parser.add_argument("-t",
    "--test-on-start",
    action="store_true",
    default=False,
    help="Run test on commits at startup")
parser.add_argument(
    "-p",
    "--project-file",
    required=True,
    help="path to JSON projects file")
parser.add_argument(
    "-v",
    "--verbose",
    default=False,
    action="store_true",
    help="Verbose on/off")
parser.add_argument(
    "-c",
    "--commit",
    default=None,
    help="only test one commit")
parser.add_argument(
    "-r",
    "--repo",
    default=None,
    help="repo to test, default is first key in project file")

args = parser.parse_args()

with open(args.project_file) as project:
    projects = json.load(project)["projects"]


for name in projects.keys():
    projects[name]["repo_handle"] = name

if args.commit is not None:
    repo = args.repo
    if repo is None:
        repo = projects.keys()[0]
    project = projects[repo]
    if args.verbose:
        print "Repo:", repo
        print "Testing Commit:", args.commit
    cibot.test_commit(project, args.commit, verbose=args.verbose)
    sys.exit()

repos = projects.keys()

if args.repo is not None:
    repos = [args.repo, ]

while True:
    for r in repos:
        p = projects[r]
        kargs = {
            "target": cibot.check_project, "args": (
                p,), "kwargs": {
                "no_test_on_startup": not args.test_on_start,
                "verbose": args.verbose}}
        t = threading.Thread(**kargs)
        t.start()
    time.sleep(args.frequency)
