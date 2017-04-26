testbot setup
======================

This repository contains all the code necessary to create a new CI
service that works with any github repository.  The setup

1. A `central` server exposed to the internet that proxies github notifications
2. One or more `tester` machines that test the repo and report
   statuses. Statuses are then picked up by the central server

ssh agents
----------

Central to the system is the ability of the machines to push to github w/o
human interaction

On Linux machines this can be done via ssh-agent

```
`eval `ssh-agent `
ssh-add ~/.ssh/id_rsa
```


Ports
-----

* 10060: for github hook
* 22: for github push


Github repository setup
-----------------------

To register a new service with Github, you must have admin access to the
github repository.  Go to the project settings page, under "Webhooks & Services"
and choose the option "Add webhook".  Point the "Payload URL" to your github proxy
service (i.e. `http://yourserver.com:10060/central`),
choose "Content type" `application/json` and you are ready to receive the events.
For security, you should create a secret key to validate requests coming from Github.

You will also need to generate an access token to give the testbot permission
to set statuses on the github repository.  You can generate one in your
user profile at [https://github.com/settings/tokens](https://github.com/settings/tokens).
Give the token a memeorable name and select only the `repo:status` checkbox.
Save the token string for later because you won't be able to access it after
you leave this page.


Central machine setup
---------------------

This repository contains a webservice implemented as a tangelo plugin.  The
service is implemented in [central/central.py](central/central.py).  You
will need to create config file in that directory named `projects.json` that
contains the following information:

```json
{
  "doutriaux1/mpas-dummy": {
      "github_webhook_secret": "****",
      "github_status_token": "*****"
      "github-events": ["push","gollum"],
      "wiki_path" : "/Users/doutriaux1/git/mpas-dummy.wiki",
      "wiki_commits_page": "COMMITS.md",
      "wiki_commits_header_lines":2,
      "wiki_commits_backlog":50,
      "wiki_testers_page": "TESTERS.md",
      "wiki_testers_header_lines":2
  }
}
```

Where: 
* `github_webhook_secret` is the secret key you setup for the webhook on github
* `github_status_token` is your personal github token
* `github-events` the github events you want to listen to (defaults to
  ["push","gollum"])
* `wiki_path` the local path on your machine where you cloned your repo's wiki
  ( `git clone git@github.com:user/repo.wiki` )
* `wiki_commits_page` is the name of the on your wiki where you want to write
  the list of commits to deal with (default to COMMITS>md if not set)
* `wiki_commits_header_lines` number of headers lines in the above page
  (default to 2 if not set)
* `wiki_commits_backlog` number of commits to keep on that page (if more
  commits are pushed to that page before the server checks again older ones
  will not be tested)
* `wiki_testers_page` name of the suffix for the wiki page where `tester`
  machine write their statuses (as to be consistent with `tester` machines
  projects (default to TESTERS.md if not set)
* `wiki_testers_header_lines` is number of headers in the above page (default
  to 2 if not set)

When that is done, install the requirements listed in [central/requirements.txt](central/requirements.txt)
and run

```
python /pth/to/this/repo/central/central.py --port=10060
--hostname=myserver.com 
```

to start the service at `http://myserver.com:10060/central`.
When the service is running, you can test the connection by a get request

```
$ curl http://myserver.com:9981
How can I help you?
```

You can obtain more help by typing:
```
python /pth/to/this/repo/central/central.py -h
```


Tester machines setup
---------------------

The tester setup is very similar to the central one.
service is implemented in [tester/listen.py](tester/listen.py).  You
will need to create config file in that directory named `projects.json` that
contains the following information:

```json
{
  "projects": {
    "doutriaux1/mpas-dummy": {
      "tester_id" : "LLNL-LOKI",
      "wiki_path" : "/git/mpas-dummy.wiki",
      "wiki_commits_page": "COMMITS.md",
      "wiki_testers_page": "TESTERS.md",
      "wiki_testers_header_lines":2,
      "wiki_backlog": 100,
      "commits_backlog": 1,
      "test_command" : "sleep 10",
      "test_execute_directory": "/Users/doutriaux1",
      "source_path": "/git/mpas-dummy",
      "simultaneous_tests": false
    }
  }
}
```

Where: 
* `tester_id` is a unique identifier that will appear in the github status and
  representing the test machine id
* `wiki_path` the local path on your machine where you cloned your repo's wiki
  ( `git clone git@github.com:user/repo.wiki` )
* `wiki_commits_page` is the name of the on your wiki where the central
  machines write the list of commits to deal with (default to COMMITS>md if not set)
* `wiki_commits_header_lines` number of headers lines in the above page
  (default to 2 if not set)
* `wiki_testers_page` name of the suffix for the wiki page where `tester`
  machine write their statuses (as to be consistent with `tester` machines
  projects (default to TESTERS.md if not set)
* `wiki_testers_header_lines` is number of headers in the above page (default
  to 2 if not set)
* `wiki_backlog` number of commits tests status to keep on that page (default
  to 256)
* `commits_backlog` number of commits to go back when checking again the commit
  page (default to 1)
* `test_command` command to run to test the repo
* `test_execute_directory` directory on tester machine where to run the test
  command from
* `source_path` directory on tester machine where the repo is cloned
* `simultaneous_tests` mutliple commits can be tested at the same time (default
  to false)
When that is done, install the requirements listed in [tester/requirements.txt](tester/requirements.txt)
and run

```
python /pth/to/this/repo/tester/listen.py -f 30
```

to start the service and check for new commits every 30 seconds
You can obtain more help by typing:
```
python /pth/to/this/repo/central/central.py -h
```

