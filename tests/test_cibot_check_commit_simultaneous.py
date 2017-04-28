import basecibot
import cibot
import time

class CIBOTTest(basecibot.CIBOTTest):
    def testCheckProject(self):
        project  = self.projects["uv-cdat/ci-bots"]
        del(project["wiki_path"])
        project["test_command"] = "dummy.bash 5"
        project["simultaneous_tests"]=False
        project["commits_backlog"]=2
        commits = cibot.get_commits(project,verbose=False)
        start = time.time()
        cibot.check_project(project,False,verbose=False)
        end = time.time()
        total = end - start
        print "Total time for 2 commits:",total
        self.assertGreater(total,10)
        self.assertLess(total,12)
        project["simultaneous_tests"]=False
        start = time.time()
        cibot.check_project(project,False,verbose=False)
        end = time.time()
        total = end - start
        print "Total time for 2 commits:",total
        self.assertLess(total,5)
