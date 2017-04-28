import unittest
import os

class CIBOTTest(unittest.TestCase):
    def setUp(self):
        self.projects = {"uv-cdat/ci-bots":
                {"tester-id":"CIBOTS",
                    "github_status_token" : "****",
                    "source_path": os.getcwd(),
                    "wiki_path": "wiki",
                    "commits_backlog" : 1,
                    "test_command" : "dummy.bash 10",
                    "test_execute_directory" : "/Users/doutriaux1",
                    "simultaneous_tests" : False
                    }}
