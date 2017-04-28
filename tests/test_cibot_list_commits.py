import basecibot
import cibot

class CIBOTTest(basecibot.CIBOTTest):
    def testListCommits(self):
        project  = self.projects["uv-cdat/ci-bots"]
        commits  = cibot.get_commits(project,verbose=False)
        self.assertEqual(len(commits),project["commits_backlog"])
