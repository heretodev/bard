




def ensure_db_dir(dbdir1,makeit):
	dbdir=os.path.join(dbdir1,".bard")
	dbmoddir = os.path.join(dbdir, MODDIR)
	if not (os.path.exists(dbdir)):
		if(makeit):
			print("Directory %s does not contain a .bard directory" % (dbdir))
			print("Making it...")
			os.makedirs(dbdir)
			os.makedirs(dbmoddir)
		else:
			raise Exception("Directory %s does not contain a .bard directory" % (dbdir))
	return dbdir

	


class BardDB(object):
	def __init__(self,root):
		self.root=root
		

