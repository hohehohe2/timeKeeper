import os
import git

class GitStorage(object):

	def __init__(self, repoPath, fileName='data'):
		self.__repo = git.Repo(repoPath)
		self.__filePath = os.path.join(repoPath, fileName)

	@staticmethod
	def isRepoReady(repoPath):
		try:
			git.Repo(repoPath)
			return True
		except:
			return False

	def save(self, binaryData, commitMessage):
		self.__repo.git.checkout('master')

		with open(self.__filePath, 'wb') as f:
			f.write(binaryData)

		self.__repo.git.add('.')
		self.__repo.git.commit(m=commitMessage)

	def load(self, hexSha):
		self.__repo.git.checkout(hexSha)
		with open(self.__filePath, 'rb') as f:
			return f.read()

	def log(self, maxCount=-1):

		if maxCount > 0:
			commits = list(self.__repo.iter_commits('master', max_count=maxCount))
		else:
			commits = list(self.__repo.iter_commits('master'))

		logs = []
		for commit in commits:
			message = commit.message
			hexSha = commit.hexsha
			date = commit.committed_date
			logs.append((message, hexSha, date))

		return logs

