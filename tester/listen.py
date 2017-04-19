import requests
import json
import threading
import subprocess
import time
import shlex
import os

commits_tested = []

with open("tester/projects.json") as project:
    projects = json.load(project)["projects"]


def process_command(cmd,path):
    print "Running:",cmd
    p = subprocess.Popen(shlex.split(cmd),cwd=path,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    print "This returned:",p.returncode
    return p.returncode

def add_commit_status(project,commit_id,status):
    print "COMMIT STATUS:",status
    process_command("git pull",project["wiki_path"])
    with open(os.path.join(project["wiki_path"],project["wiki_testers_page"])) as f:
        lines = f.readlines()[:1000]
        lines.insert(2,"%s %s %s %s\n" % (commit_id,project["tester_id"],status,time.asctime()))

    if lines[-1]!="```":
        lines.append("```")
    page = "".join(lines)
    with open(os.path.join(project["wiki_path"],project["wiki_testers_page"]),"w") as f:
        f.write(page)
    process_command("git commit -am '%s a commit'" % status,project["wiki_path"])
    process_command("git push",project["wiki_path"])


def test_commit(project,commit_id):
    print "Testing:",commit_id
    add_commit_status(project,commit_id,"pending")
    process_command("git fetch",project["source_path"])
    process_command("git checkout %s" % commit_id,project["source_path"])
    ret = process_command(project["test_command"],project["test_execute_directory"])
    if ret == 0:
        add_commit_status(project,commit_id,"success")
    else:
        add_commit_status(project,commit_id,"failure")

def check_project(name):
    project = projects[name]
    url = "http://github.com/%s/wiki/%s" % (name, project["wiki_commits_page"])
    print url
    r = requests.get(url)

    for l in r.text.split("\n")[2:2+project["commits_backlog"]]:
        print l
        commit_id = l.split()[0]
        if not commit_id in commits_tested:
            commits_tested.insert(0,commit_id)
            if project["simultaneous_tests"]:
                kargs = {"target":test_commit,"args":(project,commit_id)}
                print "THREASDING"
                t = threading.Thread(**kargs)
                t.start()
            else:
                test_commit(project,commit_id)

if __name__ == "__main__":
    check_project("doutriaux1/mpas-dummy")
