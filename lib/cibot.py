import requests
import json
import threading
import subprocess
import shlex
import os


def process_command(cmd, path=os.getcwd(), verbose=True):
    if verbose:
        print "Running", cmd, "in", path
    out = subprocess.PIPE
    err = subprocess.STDOUT
    if verbose:
        print "\t\tLOG FILE :", out
    p = subprocess.Popen(shlex.split(cmd), cwd=path, stdout=out, stderr=err)
    o, e = p.communicate()
    if verbose:
        print "\t\tCOMMUNICATE DONE"
    if verbose:
        print "\t\tRETURN CODE:", p.returncode
    return p.returncode, o


def write_to_wiki(project, commit_id, log, verbose=True):
    logfile = os.path.join(project["tester_id"], commit_id)
    logfile_pth = os.path.join(
        project["wiki_path"],
        project["tester_id"],
        commit_id)
    if not os.path.exists(os.path.join(
            project["wiki_path"], project["tester_id"])):
        os.makedirs(os.path.join(project["wiki_path"], project["tester_id"]))
    with open(logfile_pth, "w") as f:
        f.write(log)

    failed = True
    while failed:
        process_command("git pull", project["wiki_path"])
        process_command("git reset --hard origin/master", project["wiki_path"])
        process_command("git add %s" % logfile, project["wiki_path"])
        process_command(
            "git commit -am 'adding log for commit %s'" %
            commit_id, project["wiki_path"])
        ret, log = process_command("git push", project["wiki_path"])
        if verbose:
            print "returned:", ret
        if ret == 0:  # Pushed successfully getting out
            failed = False


def test_commit(project, commit_id, verbose=True):
    if verbose:
        print "\tTESTING COMMIT:", commit_id
    add_commit_status(project, commit_id, "pending")
    process_command("git fetch", project["source_path"])
    process_command("git checkout %s" % commit_id, project["source_path"])
    ret, log = process_command(
        project["test_command"], project["test_execute_directory"],
        verbose=verbose)

    write_to_wiki(project, commit_id, log, verbose=verbose)

    if verbose:
        print "COMMAND TESTING RETURNED", ret
    if ret == 0:
        add_commit_status(project, commit_id, "success")
    else:
        add_commit_status(project, commit_id, "failure")


def add_commit_status(project, commit_id, state):
    tester = project["tester_id"]
    statuses_url = "https://api.github.com/repos/%s/statuses/%s" % (
        project["github_repo"], commit_id)
    target_url = "https://github.com/%s/wiki" % project["github_repo"]
    headers = {"Authorization": "token %s" % project["github_status_token"]}
    data = {
        "state": state,
        "target_url": "%s/%s/%s" % (target_url, tester, commit_id),
        "description": "%s test" % tester,
        "context": "cont-int/%s" % tester
    }
    resp = requests.post(
        statuses_url,
        data=json.dumps(data),
        verify=False,
        headers=headers)
    return resp


def get_commits(project, verbose=True):
    process_command("git pull", project["source_path"])
    n = project.get("commits_backlog", 5)
    if verbose:
        print "Checking the last %i commits" % n
    ret, log = process_command(
        "git rev-list --remotes -n %i" %
        n, project["source_path"])
    commits = log.split("\n")
    return commits


commits_tested = []
first_pass = {}


def check_project(project, verbose=True):
    name = project["github_repo"]
    if verbose:
        print "Checking:", project["github_repo"]
    commits = get_commits(project, verbose)
    for commit_id in commits:
        if verbose:
            print "CHECKING FOR COMMIT:", commit_id
        if not (name, commit_id) in commits_tested:
            if verbose:
                print "\tNOT TESTED"
            commits_tested.insert(0, (name, commit_id))
            if first_pass.get(name, True) is False:
                if project["simultaneous_tests"]:
                    kargs = {
                        "target": test_commit, "args": (
                            project, commit_id), "kwargs": {
                            "verbose": verbose}}
                    t = threading.Thread(**kargs)
                    t.start()
                else:
                    test_commit(project, commit_id, verbose=verbose)
            else:
                if verbose:
                    print "\tBUT SKIPPED BECAUSE THIS IS THE FIRST PASS"
        else:
            if verbose:
                print "\tAlready tested"

    first_pass[name] = False
