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


# load a projects file
# see https://developer.github.com/webhooks/#events

_projects_file = os.path.join(os.path.dirname(__file__), 'projects.json')
with open(_projects_file) as f:
    projects = json.load(f)['projects']

def authenticate(key, body, received):
    """Authenticate an event from github."""
    computed = hmac.new(str(key), body, hashlib.sha1).hexdigest()
    print "RECEIVED:",received
    print "computed:",computed
    # The folowing func does not exist on my home mac
    # trapping in try/except
    try:
      print "COMPARE:",hmac.compare_digest(computed, received)
      return hmac.compare_digest(computed, received)
    except Exception,err:
      print "EXCETPED:",err
      return computed == received


def get_project(name):
    """Return the object from `projects` matching `name` or None."""
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
    print "Do we even vome in here?"
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
    print "MASTER RECEIVED A POST EVENT",arg,kwarg
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
    print "project name:",project_name
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
    update_wiki_commit(project["wiki_path"],commit)

def process_wiki(obj):
    pages = obj["pages"]
    print "PROCESSING WIKI"
    project_name = obj.get('repository', {}).get('full_name')
    print "project name:",project_name
    project = get_project(project_name)
    for page in pages:
        if page["page_name"]+".md" == project["wiki_testers_page"]:
            headers = {}
            #headers = {"Authorization":"token %s" % project["github_status_token"]}
            process_command("git pull",project["wiki_path"])
            with open(os.path.join(project["wiki_path"],project["wiki_testers_page"])) as f:
                lines = f.readlines()
                processed = []
                for line in lines[2:]:
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
                       print "psoting:",data
                       print "posting to:",obj["repository"]["statuses_url"].replace("{sha}",commit_id)
                       resp = requests.post(
                               obj["repository"]["statuses_url"].replace("{sha}",commit_id),
                               data = json.dumps(data),
                               verify = False,
                               headers = headers)
                       print "POSTED A",state,"event response was:",resp.status_code
                    processed.append((commit_id,tester))

    return


def process_command(cmd,path):
    p = subprocess.Popen(shlex.split(cmd),cwd=path)
    p.communicate()
    return p.returncode

def update_wiki_commit(path,commit):
    fnm = os.path.join(path,"COMMITS.md")
    with open(fnm) as f:
        commits = f.readlines()[:50]
        commits.insert(2,"%s %s %s\n" % (commit["id"],commit["author"]["username"],commit["message"].split("\n")[0][:25]))
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
    update_wiki_commit("/Users/doutriaux1/git/mpas-dummy.wiki",{"id":"121234324234","author":{"username":"doutriaux1"},"message":"my long commit is here"})


def crap():
      context = "cont-int/LLNL/%s-%s" % (obj["os"],obj["slave_name"])
      data = {
          "state":state,
          "target_url": target,
          "description": "'%s' (%s)" % (obj["command"][:20],time.asctime()),
          "context": context,
          }
      resp = requests.post(
          obj["commit"]["statuses_url"].replace("{sha}",obj["commit"]["id"]),
          data = json.dumps(data),
          verify = False,
          headers = headers)

      return "Received and treated a BOT STATUS update event"


def cmd2str(command):
  return "__".join(command.split()[:3]).replace("/","_")
