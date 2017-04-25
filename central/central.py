#!/usr/bin/env python

"""Tangelo application that proxy's github events to buildbot."""

import os
import json
import hmac
import hashlib

import tangelo
import requests

import time
import subprocess
import shlex

_projects_file = os.environ.get("PROJECTS_FILE")
if _projects_file is not None:
    with open(_projects_file) as f:
        projects = json.load(f)

def authenticate(key, body, received):
    """Authenticate an event from github."""
    computed = hmac.new(str(key), body, hashlib.sha1).hexdigest()
    # The folowing func does not exist on my home mac
    # trapping in try/except
    try:
      return hmac.compare_digest(computed, received)
    except Exception,err:
      return computed == received


def get_project(name):
    """Return the object from `projects` matching `name` or None."""
    global projects
    return projects.get(name)


def forward(slave,obj,signature):
    """Forward an event object to the configured buildbot instance."""

    resp = requests.post(
        slave,
        data=json.dumps(obj),
        headers={"BOT-Signature":"sha1:%s" % signature,
          "BOT-Event":"status",
          }
    )
    #    headers={'CONTENT-TYPE': 'application/x-www-form-urlencoded'}

    return resp


@tangelo.restful
def get(*arg, **kwarg):
    """Make sure the server is listening."""
    if len(arg)>0:
      try:
        project = get_project("%s/%s" % arg[1:3])
        pth = os.path.join(*arg)
        pth = os.path.join(project["logs_dir"],pth)
        f=open(pth)
        msg = f.read()
        f.close()
      except Exception,err:
        msg = 'How can I help you?\n%s,%s\n%s' % (arg,kwarg,err)
    else:
      msg = 'How can I help you?\n'
    tangelo.content_type("text/html")
    return msg


@tangelo.restful
def post(*arg, **kwarg):
    """Listen for github webhooks, authenticate, and forward to buildbot."""
    # retrieve the headers from the request
    # print "TGELO CONFI",tangelo.cherrypy.request.header_list
    try:
        received = tangelo.request_header('X-Hub-Signature')[5:]
    except Exception:
        received = ''

    # get the request body as a dict
    # for json
    body = tangelo.request_body().read()

    try:
        obj = json.loads(body)
    except:
        tangelo.http_status(400, "Could not load json object")
        return "Could not load json object"

    # obj = json.loads(kwarg['payload'])
    #open('last.json', 'w').write(json.dumps(obj, indent=2))
    project_name = obj.get('repository', {}).get('full_name')
    project = get_project(project_name)
    if project is None:
        tangelo.http_status(400, "Unknown project")
        return 'Unknown project'

    # make sure this is a valid request coming from github
    if not authenticate(project.get('github_webhook_secret', ''), body, received):
        tangelo.http_status(403, "Invalid signature")
        return 'Invalid signature'

    event = tangelo.request_header('X-Github-Event')
    print "EVENT:",event

    if project['github-events'] == '*' or event in project['github-events']:
        obj['event'] = event
        if event == "push":
            process_push(obj)
        elif event == "gollum":
            process_wiki(obj)
    else:
        tangelo.http_status(200, "Unhandled event")
        return 'Unhandled event'
def process_push(obj):
    try:
      commit = obj["head_commit"]
      is_commit = True
    except:
      commit = obj["pull_request"]
      is_commit = False
    project_name = obj.get('repository', {}).get('full_name')
    project = get_project(project_name)
    update_wiki_commit(project,commit)

def process_wiki(obj):
    pages = obj["pages"]
    project_name = obj.get('repository', {}).get('full_name')
    project = get_project(project_name)
    headers = {"Authorization":"token %s" % project["github_status_token"]}
    testers_page = project.get("wiki_testers_page","TESTERS.md")
    for page in pages:
        if (page["page_name"]+".md").find(testers_page)>-1:
            process_command("git pull",project["wiki_path"])
            with open(os.path.join(project["wiki_path"],page["page_name"]+".md")) as f:
                lines = f.readlines()
                processed = []
                for line in lines[project.get("wiki_testers_header_lines",2):-1]:
                    sp = line.split()
                    commit_id = sp[0]
                    tester = sp[1]
                    state = sp[2]
                    if not (commit_id,tester) in processed:
                       data = {
                               "state": state,
                               "target_url": "%s/wiki/%s/%s" % (obj["repository"]["html_url"],tester,commit_id),
                               "description": "%s test" % tester,
                               "context": "cont-int/%s" % tester
                               }
                       resp = requests.post(
                               obj["repository"]["statuses_url"].replace("{sha}",commit_id),
                               data = json.dumps(data),
                               verify = False,
                               headers = headers)
                    processed.append((commit_id,tester))

    return


def process_command(cmd,path=os.getcwd(),verbose=False, env=os.environ):
    if verbose:
        print "Running",cmd
    p = subprocess.Popen(shlex.split(cmd),cwd=path,env=env)
    p.communicate()
    return p.returncode

def update_wiki_commit(project,commit):
    path = project["wiki_path"]
    fnm = os.path.join(path,project.get("wiki_commits_page","COMMITS.md"))
    backlog = project.get("wiki_commits_backlog",50)
    with open(fnm) as f:
        commits = f.readlines()[:backlog]
        commits.insert(2,"%s %s %s %s\n" % (commit["id"],commit["author"]["username"],time.asctime(),commit["message"].split("\n")[0][:25]))
    # Make sure last line closes pre block
    if commits[-1]!="```":
        commits.append("```")
    lst = "".join(commits)

    f=open(fnm,"w")
    f.write("".join(commits))
    f.close()
    process_command("git commit -am 'updated list of commit'",path)
    process_command("git push",path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Starts a tangelo server to listen to github webhook')
    parser.add_argument("-p","--project-file",default=os.path.join(os.path.dirname(__file__), 'projects.json'),help="path to JSON projects file")
    parser.add_argument("-P","--port",default=60010,type=int,help="port to listen webhook on")
    parser.add_argument("-H","--hostname",default=os.uname()[1],help="hostname")

    args=parser.parse_args()

    # load a projects file
    # see https://developer.github.com/webhooks/#events
    _projects_file = os.path.join(args.project_file)
    myenv = os.environ
    myenv["PROJECTS_FILE"]=_projects_file

    cmd = "tangelo -r %s --hostname %s --port=%i" % (os.path.dirname(__file__),args.hostname,args.port)
    process_command(cmd,env = myenv)
