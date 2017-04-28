import basecibot
import cibot

class CIBOTTest(basecibot.CIBOTTest):
    def testCheckCommits(self):
        project  = self.projects["uv-cdat/ci-bots"]
        del(project["wiki_path"])
        print "PTH:",project["test_execute_directory"]
        print "PTH:",project["source_path"]
        commits = cibot.get_commits(project,verbose=False)
        ret,log = cibot.test_commit(project,commits[0],verbose=False)
        self.assertEqual(ret,0)
        print log
        # Making sure it is an ls -l
        self.assertEqual(len(log.split("\n")[-2].split()),9)
