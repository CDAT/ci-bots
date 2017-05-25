

# <img src="https://cloud.githubusercontent.com/assets/4295853/26455216/cd8f3c2a-4126-11e7-9419-590882061f47.png" width="200">  Continous Improvement testbot (CI-bot)

This repository contains all the code necessary to create a new CI service.
At the moment is has support for github statuses and uses github wiki for
commit test logs.

ssh agent setup
----------

Central to the system is the ability of the machines to push to github without
human interaction.

On Linux machines this can be done via the ssh-agent:

```
eval `ssh-agent `
ssh-add ~/.ssh/id_rsa
```

Tester machine setup
---------------------

In order to use to push to statuses you will need to create a personal token on
github

Go into your settings under your profile
Click on `Personal access token`
Click on `Generate new token`
Enter a description in 
Check the `repo` box
Copy the token key and put it in the `hithub_status_token` section bellow

The tester setup is fairly easy.
You will need to create json config file in the tester directory.
That json file contains the following information:

```json
{
  "projects": {
    "doutriaux1/mpas-dummy": {
      "tester_id" : "LLNL-LOKI",
      "github_status_token" : "*****",
      "source_path" : "/git/mpas-dummy",
      "wiki_path" : "/git/mpas-dummy.wiki",
      "commits_backlog" : 1,
      "test_command" : "dummy.bash 10",
      "test_execute_directory" : "/Users/doutriaux1",
      "simultaneous_tests" : false
    }
  }
}
```

Where:
* "doutriaux1/mpas-dummy" is the github repo you wish to test
* `tester_id` is a unique identifier that will appear in the github status and
  representing the test machine id
* `github_status_token` is your personal github token
* `source_path` directory on tester machine where the repo is cloned
* `wiki_path` the local path on your machine where you cloned your repo's wiki
  ( `git clone git@github.com:user/repo.wiki` ) repo mustbe writable
* `commits_backlog` number of commits to go back
* `test_command` command to run to test the repo
* `test_execute_directory` directory on tester machine where to run the test
  command from
* `simultaneous_tests` mutliple commits can be tested at the same time (default
  to false)

When that is done, install the requirements listed in [requirements.txt](requirements.txt)

Install this into your python

```
python setup.py install
```

to start the service and check for new commits every 30 seconds

```
ci-bot -p project.json -f 30
```

You can also test a single commit by runnnig:

```
ci-bot -p project.json -c **YOUR_COMMIT_SHA1** -r **REPO_HANDLE**
```

You can obtain more help by typing:
```
ci-bot -h
```

