import unittest
import os
import cibot

class CIBOTTest(unittest.TestCase):
    def setUp(self):
        self.projects = {"uv-cdat/ci-bots":
                {"tester_id":"CIBOTS",
                    "repo_handle":"uv-cdat/ci-bots",
                    "source_path": os.path.join(os.getcwd(),"tests","clone-repo"),
                    "wiki_path": os.path.join(os.getcwd(),"tests","clone-wiki"),
                    "commits_backlog" : 1,
                    "test_command" : "dummy.bash 3",
                    "test_execute_directory" : os.path.dirname(__file__),
                    "simultaneous_tests" : False
                    }}

        project = self.projects["uv-cdat/ci-bots"]
        if not os.path.exists(os.path.dirname(project["source_path"])):
            os.path.makedirs(os.path.dirname(project["source_path"]))
        if not os.path.exists(project["source_path"]):
            cibot.process_command("git clone git://github.com/%s clone-repo" % project["github_repo"],os.path.dirname(project["source_path"]),verbose=False)
        if not os.path.exists(project["wiki_path"]):
            cibot.process_command("git clone git://github.com/%s.wiki clone-wiki" % project["github_repo"],os.path.dirname(project["wiki_path"]),verbose=False)

            
