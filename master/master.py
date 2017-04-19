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
    if not authenticate(project.get('api-key', ''), body, received):
        tangelo.http_status(403, "Invalid signature")
        return 'Invalid signature'

    event = tangelo.request_header('X-Github-Event')
    print "EVENT:",event

    if project['github-events'] == '*' or event in project['github-events']:
        obj['event'] = event
        try:
          commit = obj["head_commit"]
          is_commit = True
        except:
          commit = obj["pull_request"]
          is_commit = False
        print "commit was:",commit
        update_wiki_commit(project["wiki_path"],commit)
    else:
        tangelo.http_status(200, "Unhandled event")
        return 'Unhandled event'


def update_wiki_commit(path,commit):
    fnm = os.path.join(path,"COMMITS.md")
    with open(fnm) as f:
        commits = f.readlines()[:50]
        commits.insert(1,"%s %s %s" % (commit["id"],commit["author"]["username"],commit["message"].split("\n")[0][:25]))
    f=open(fnm,"w")
    f.write("\n".join(commits))
    f.close()
    subprocess.call(shlex.split("git commit -am 'updated list of commit'"))
    subprocess.call(shlex.split("git push"))


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
