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

def process_command(cmd,path,verbose=False):
    if verbose:
        print "Running",cmd
    p = subprocess.Popen(shlex.split(cmd),cwd=path,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    return p.returncode

def add_commit_status(project,commit_id,status):
    process_command("git pull",project["wiki_path"])
    testers_page = project.get("wiki_testers_page","TESTERS.md")
    with open(os.path.join(project["wiki_path"],testers_page)) as f:
        lines = f.readlines()[:project.get("wiki_backlog",256)]
        lines.insert(project.get("wiki_testers_header_lines",2),"%s %s %s %s\n" % (commit_id,project["tester_id"],status,time.asctime()))

    if lines[-1]!="```":
        lines.append("```")
    page = "".join(lines)
    with open(os.path.join(project["wiki_path"],testers_page),"w") as f:
        f.write(page)
    process_command("git commit -am '%s a commit'" % status,project["wiki_path"])
    process_command("git push",project["wiki_path"])


def test_commit(project,commit_id):
    print "TESTING COMMIT:",commit_id
    add_commit_status(project,commit_id,"pending")
    process_command("git fetch",project["source_path"])
    process_command("git checkout %s" % commit_id,project["source_path"])
    ret = process_command(project["test_command"],project["test_execute_directory"],verbose=True)
    if ret == 0:
        add_commit_status(project,commit_id,"success")
    else:
        add_commit_status(project,commit_id,"failure")

def check_project(name):
    print "Checking:",name
    project = projects[name]
    url = "http://github.com/%s/wiki/%s" % (name, project["wiki_commits_page"])
    r = requests.get(url,verify=False)
    commits_headers = project.get("wiki_commit_header_lines",2)
    for l in r.text.split("\n")[commits_headers:commits_headers+project["commits_backlog"]]:
        commit_id = l.split()[0]
        if not (name, commit_id) in commits_tested:
            commits_tested.insert(0,(name, commit_id))
            if first_pass.get(name,True) is False:
                if project["simultaneous_tests"]:
                    kargs = {"target":test_commit,"args":(project,commit_id)}
                    t = threading.Thread(**kargs)
                    t.start()
                else:
                    test_commit(project,commit_id)

    first_pass[name] = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Listens for requested CI')
    parser.add_argument("-f","--frequency",help="Frequency at which to check for new ommits to test",type=int,default=5)
    parser.add_argument("-p","--project-file",default=os.path.join(os.path.dirname(__file__), 'projects.json'),help="path to JSON projects file")
    args=parser.parse_args()

    commits_tested = []

    with open(args.project_file) as project:
        projects = json.load(project)["projects"]

    while True:
        for p in projects.keys():
            kargs = {"target":check_project,"args":(p,)}
            t = threading.Thread(**kargs)
            t.start()
        time.sleep(args.frequency)
