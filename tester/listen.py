import requests
import json
import threading
import subprocess
import time
import shlex
import os
import argparse
import sys

first_pass = {}
verbose = False

def process_command(cmd,path,verbose=False,log=None):
    if verbose:
        print "Running",cmd
    if log is None:
        out = subprocess.PIPE
    else:
        out = open(log,"w")
    if verbose:
        print "\t\tLOG FILE :",out
    p = subprocess.Popen(shlex.split(cmd),cwd=path,stdout=out, stderr=out)
    p.communicate()
    if verbose:
        print "\t\tCOMMUNICATE DONE"
    if log is not None:
        out.close()
    if verbose:
        print "\t\tRETURN CODE:",p.returncode
    return p.returncode

def add_commit_status(project,commit_id,status):
    #process_command("git pull",project["wiki_path"])
    #process_command("git reset --hard origin/master",project["wiki_path"])
    testers_page = "%s.%s" % (project["tester_id"],project.get("wiki_testers_page","TESTERS.md"))
    testers_page_pth = os.path.join(project["wiki_path"],testers_page)
    headers = project.get("wiki_testers_header_lines",2)
    if not os.path.exists(testers_page_pth):
        if not os.path.exists(os.path.dirname(testers_page_pth)):
            os.makedirs(os.path.dirname(testers_page_pth))
        with open(testers_page_pth,"w") as f:
            print "CREATED:",headers,f
            if headers == 1:
                n = 0
            elif headers > 1:
                f.write("Lists of commits tested\n")
                n = 1
            while n<headers-1:
                f.write("\n")
                n = n + 1

            f.write( "```\n")
            f.write( "```")
            f.close()

        process_command("git add %s" % testers_page_pth,project["wiki_path"])

    with open(testers_page_pth) as f:
        lines = f.readlines()[:headers+project.get("wiki_backlog",256)]
        print "LINRES:",lines
        lines.insert(headers,"%s %s %s %s\n" % (commit_id,project["tester_id"],status,time.asctime()))

    if lines[-1]!="```":
        lines.append("```")
    page = "".join(lines)
    with open(os.path.join(project["wiki_path"],testers_page),"w") as f:
        f.write(page)
    process_command("git commit -am '%s a commit'" % status,project["wiki_path"])
    process_command("git push --force",project["wiki_path"],verbose=True)


def test_commit(project,commit_id):
    if verbose:
        print "\tTESTING COMMIT:",commit_id
    process_command("git pull",project["wiki_path"])
    process_command("git reset --hard origin/master",project["wiki_path"])
    add_commit_status(project,commit_id,"pending")
    process_command("git fetch",project["source_path"])
    #process_command("git reset --hard origin/master",project["source_path"])
    process_command("git checkout %s" % commit_id,project["source_path"])
    logfile = os.path.join(project["wiki_path"],project["tester_id"],commit_id)
    if not os.path.exists(os.path.join(project["wiki_path"],project["tester_id"])):
        os.makedirs(os.path.join(project["wiki_path"],project["tester_id"]))
    ret = process_command(project["test_command"],project["test_execute_directory"],verbose=True, log=logfile)
    process_command("git pull",project["wiki_path"])
    process_command("git reset --hard origin/master",project["wiki_path"])
    process_command("git add %s" % logfile,project["wiki_path"],verbose=True)
    if verbose:
        print "COMMAND TESTING RETURNED",ret,"------------------------------------"
    if ret == 0:
        add_commit_status(project,commit_id,"success")
    else:
        add_commit_status(project,commit_id,"failure")

def check_project(name):
    if verbose:
        print "Checking:",name
    project = projects[name]
    process_command("git pull",project["wiki_path"])
    fnm = os.path.join(project["wiki_path"], project["wiki_commits_page"])
    with open(fnm) as f:
        r = f.read()
    commits_headers = project.get("wiki_commit_header_lines",2)
    commits_backlog = project.get("commits_backlog",1)
    if verbose:
        print "CHECKING THE LAST %i commits" % commits_backlog
    for l in r.split("\n")[commits_headers:commits_headers+commits_backlog]:
        commit_id = l.split()[0]
        if verbose:
            print "CHECKING FOR COMMIT:",commit_id
        if not (name, commit_id) in commits_tested:
            if verbose:
                print "\tNOT TESTED"
            commits_tested.insert(0,(name, commit_id))
            if first_pass.get(name,True) is False:
                if project["simultaneous_tests"]:
                    kargs = {"target":test_commit,"args":(project,commit_id)}
                    t = threading.Thread(**kargs)
                    t.start()
                else:
                    test_commit(project,commit_id)
            else:
                if verbose:
                    print "\tBUT SKIPPED BECAUSE THIS IS THE FIRST PASS"
        else:
            if verbose:
                print "\tAlready tested"

    first_pass[name] = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Listens for requested CI')
    parser.add_argument("-f","--frequency",help="Frequency at which to check for new ommits to test",type=int,default=5)
    parser.add_argument("-p","--project-file",default=os.path.join(os.path.dirname(__file__), 'projects.json'),help="path to JSON projects file")
    parser.add_argument("-v","--verbose",default=False,action="store_true",help="Verbose on/off")
    args=parser.parse_args()
    verbose = args.verbose

    commits_tested = []

    with open(args.project_file) as project:
        projects = json.load(project)["projects"]

    while True:
        for p in projects.keys():
            kargs = {"target":check_project,"args":(p,)}
            t = threading.Thread(**kargs)
            t.start()
        time.sleep(args.frequency)
