def import_cmd(args):
	dbdir=ensure_db_dir(args.db,True)

	for impdir in args.targets:
		impdir=os.path.abspath(impdir)
		import_db_dir(dbdir,impdir)


def mount_cmd(args):
	dbdir=ensure_db_dir(args.db,False)
	create_symlink_file_tree_from_db(dbdir, args.mountdir)

def fingerprint_cmd(args):
	dbdir=ensure_db_dir(args.db,False)
	do_fingerprint(dbdir,args.type)

if(__name__=="__main__"):
	parser = argparse.ArgumentParser()
	base_parser = argparse.ArgumentParser(add_help=False)
	base_parser.add_argument("--db","-d",type=str,default=os.getcwd(),help="the directory containing the database (.bard) dir")
	subparsers = parser.add_subparsers(dest="cmd")

	import_parser=subparsers.add_parser('import', help='import files and directories into bard',parents=[base_parser])
	import_parser.add_argument('targets', type=str,help='the files and folders to import',nargs='+')
	import_parser.set_defaults(cmdfunc=import_cmd)

	mount_parser=subparsers.add_parser('ln', help='mount bard files into a symlink',parents=[base_parser])
	mount_parser.add_argument('mountdir', help='The target directory to make a symlink into')
	mount_parser.set_defaults(cmdfunc=mount_cmd)

	fingerprint_parser=subparsers.add_parser("fingerprint",help="fingerprint files inside bard based on content",parents=[base_parser])
	fingerprint_parser.add_argument("--type","-t",action='append',default='all',choices=['all','image'],help="the type of fingerprinting to do")
	fingerprint_parser.set_defaults(cmdfunc=fingerprint_cmd)

	#parser.add_argument("-f", "--fingerprint", help="compute and store image content hashes to metadata json in bard imported files")
	args = parser.parse_args()
	if(args.cmd is None):
		parser.print_help()
	else:
		return args.cmdfunc(args)

