from PIL import Image
import imagehash
import json
import os
import shutil
import hashlib
import datetime
import base64
import argparse
import math
import subprocess
from pathlib import Path # Python3.5 onward (for progress bar in import)
from tqdm import tqdm # progress bar

HASH_SUBDIR_LEN = 3
MODHASH_SUBDIR_LEN = 3
MODDIR = "mod"
IMAGE_EXTENSIONS = [".jpg", ".png", ".jpeg", ".bmp", ".pgm", ".ppm", ".tiff"]

### HASH COMPUTATION FUNCTIONS: 
def secure_hash_filepath(filepath):
	process = subprocess.Popen(["b2sum", "-l", "256", "-b", filepath], stdout=subprocess.PIPE)
	line = process.stdout.readline()
	for ind,ch in enumerate(line):
		if ((ch == ord(" ")) or (ch == ord("\n"))):
			hash = line[0:ind]
			return base64.b64encode(hash).decode("ascii")

def secure_hash(s):
	gfg = hashlib.blake2b() # need to create fresh for each hash
	gfg.update(s)
	hash = gfg.digest()
	return base64.b64encode(hash).decode("ascii").replace('/', '')

def compute_modhash(path):
	canonical_device_id=""#TODO: identify_hard_drive_hardware_device_identifier #bard/path_identifier.py ...the windows code isn't finished but I rmemeber it was possible to find one that worked cross platform.
	canonical_path_in_device = path  #(but remove any leading prefix like "C:" or "/media/steven" and also turn all "\" into "/"]
	mtime = os.path.getmtime(path)
	mtime_utc = datetime.datetime.utcfromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
	modstr = canonical_device_id+"|"+canonical_path_in_device+"|"+mtime_utc
	modhash = secure_hash(modstr.encode('utf-8'))
	return modhash



def compute_content_hash(f, ext):
	hash = secure_hash_filepath(f)
	return hash

### METADATA FUNCTIONS: ONE UNIQUE PER CONTENT HASH
def load_metadata(metadatapath):
	metadata = {}
	if os.path.exists(metadatapath):
		with open(metadatapath) as mf:
			metadata = json.load(mf)
	return metadata

def write_content_metadata(metadatapath, metadata):
	with open(metadatapath, 'w') as mf:
		json.dump(metadata, mf)

def init_or_update_content_metadata(metadatapath, f, hash, modhash):
	metadata = {}
	# read the existing metadata file (handle case if missing)
	if os.path.exists(metadatapath):
		metadata = load_metadata(metadatapath)
		if not(f in metadata["filenames"]):
			metadata["filenames"].append(f)
		metadata["modhash"] = modhash
	else:
		metadata = {"hash":"%s" % hash, "filenames":[f], "modhash" : modhash}
	return metadata

# Update file + metadata, copy file to if not there or different modhash.
def update_file_entry(file_path, dbdir, same_content_hash_overwrite_with_new = True):
	ext = os.path.splitext(file_path)[1] # Note: still works on no extension files
	metadata = {}
	modhash = compute_modhash(file_path)

	# Look for modhash file to get precomputed content hash.  Compute content hash if not found.
	new = False
	modhash_dir = os.path.join(os.path.join(dbdir, MODDIR), modhash[0:MODHASH_SUBDIR_LEN])
	modhash_path = os.path.join(modhash_dir, modhash)
	if(not os.path.exists(modhash_dir) or not os.path.exists(modhash_path)):
		new = True
		hash = compute_content_hash(file_path,ext)
	else:
		with open(modhash_path) as f:
			hash = f.readlines()[0]
	db_hash_dir = os.path.join(dbdir, ("%s" % hash)[0:HASH_SUBDIR_LEN])

	if not new:
		metadatapath = os.path.join(db_hash_dir, ("%s.json" % hash))
		metadata = load_metadata(metadatapath)

	# Copy file named as content hash + extension if it doesn't exist or it's old
	update_metadata = False
	db_copy_path = os.path.join(db_hash_dir, ("%s" % hash) + ext)
	if not os.path.exists(db_copy_path) or (same_content_hash_overwrite_with_new and (len(metadata)) and (modhash != metadata["modhash"])):
		# mod time updated: generate fresh content hash
		if(len(metadata) and (modhash != metadata["modhash"])):
			hash = compute_content_hash(file_path, ext)
			db_copy_path = os.path.join(db_hash_dir,("%s" % hash) + ext)
		if not(os.path.exists(db_hash_dir)):
			os.makedirs(db_hash_dir)
		shutil.copy2(file_path, db_copy_path) # copy2 gets metadata too
		update_metadata = True
	if (len(metadata) and not (file_path in metadata["filenames"])):
		update_metadata = True

	if update_metadata:
		# Update (or create) metadata for hash:
		metadatapath = os.path.join(db_hash_dir, ("%s.json" % hash)) # if path not set before
		metadata = init_or_update_content_metadata(metadatapath, file_path, hash, modhash)
		write_content_metadata(metadatapath, metadata)

		# Create modhash entry for db:
		modhash_dir = os.path.join(os.path.join(dbdir, MODDIR), modhash[0:MODHASH_SUBDIR_LEN])
		if(not os.path.exists(modhash_dir)):
			os.makedirs(modhash_dir)
		modhash_path = os.path.join(modhash_dir, modhash)
		with open(modhash_path, "w") as f:
			f.write("%s" % hash)

	# info from file: all metadata is indexed by content hash. (hash, other filenames, modhash)
	return modhash, "%s" % hash

def import_db_dir(importdir, progress_bar = None, total_files = 0, display_recursive_progress = True):
	if (display_recursive_progress) and (total_files == 0):
		total_files = len([path for path in Path(importdir).rglob('*')])
		progress_bar = tqdm(range(total_files), desc="Importing...", unit=" files")

	files = [os.path.join(importdir,f) for f in os.listdir(importdir) if os.path.isfile(os.path.join(importdir, f))]
	# TODO: subprocess to split up hashing for initial import SPEED!
	for f in files:
		#print('processing:', f)
		if display_recursive_progress:
			progress_bar.update(1)

		modhash, hash = update_file_entry(f, dbdir)
	dirs = [os.path.join(importdir,f) for f in os.listdir(importdir) if os.path.isdir(os.path.join(importdir, f))]
	for d in dirs:
		#print('recursing to dir:', d)
		if display_recursive_progress:
			progress_bar.update(1) # Note: Total files glob counts directories as files, so recursing increases the processed count
		progress_bar = import_db_dir(d, progress_bar, total_files)
	return progress_bar

### SYMLINK FUNCTIONS: only load db map of modhash->content hash for symlink.
def load_db_from_mod(db_mod_dir):
	db = {}
	for modhash_dir in os.listdir(db_mod_dir):
		db_modhash_dir = os.path.join(db_mod_dir, modhash_dir)
		for modhash in os.listdir(db_modhash_dir):
			with open(os.path.join(db_modhash_dir, modhash)) as f:
				hash = f.readlines()[0]
				db[modhash] = hash
	return db

def create_symlink_file_tree_from_db(mountdir, dbdir):
	dbdir = os.path.abspath(dbdir)
	dbmoddir = os.path.join(dbdir, MODDIR)
	db = load_db_from_mod(dbmoddir)
	if not (os.path.exists(mountdir)):
		os.makedirs(mountdir)
	# first, get common root directory and strip it out to get base directory to copy
	# get list of filenames from metadata files:  #TODO: filter this by passing in a subdirectory of interest to mount rather than mounting the whole db
	filenames = []
	for _, hash in db.items():
		db_hash_dir = os.path.join(dbdir, ("%s" % hash)[0:HASH_SUBDIR_LEN])
		metadatapath = os.path.join(db_hash_dir, "%s.json" % hash)
		metadata = load_metadata(metadatapath)
		for f in metadata["filenames"]:
			filenames.append(f)
	root = os.path.commonpath(filenames)

	# super slow to reload all the metadata files:
	for _,hash in db.items():
		db_hash_dir = os.path.join(dbdir, ("%s" % hash)[0:HASH_SUBDIR_LEN])
		metadatapath = os.path.join(db_hash_dir, "%s.json" % hash)
		metadata = load_metadata(metadatapath)
		for f in metadata["filenames"]:
			inside_root_path = f[len(root)+1:]
			dst_path = os.path.join(mountdir, inside_root_path)
			dst_dir = os.path.dirname(dst_path)
			if not (os.path.exists(dst_dir)):
				os.makedirs(dst_dir)
			ext = os.path.splitext(inside_root_path)[1]
			src_path = os.path.join(db_hash_dir, hash + ext)
			os.symlink(src_path, dst_path)

def do_fingerprint(dbdir):
	modhash_files = len([path for path in Path(os.path.join(dbdir, MODDIR)).rglob('*')])
	total_files = modhash_files - 1
	progress_bar = tqdm(range(total_files), desc="Fingerprinting...", unit=" files")
	for db_hash_dir in os.listdir(dbdir):
		if(db_hash_dir == MODDIR):
			continue
		for hash_file in os.listdir(os.path.join(dbdir, db_hash_dir)):
			hash, ext = os.path.splitext(hash_file)
			if (not (ext == ".json")): # only process metadata files since loop over all file extension types is inside here:
				continue
			metadatapath = os.path.join(os.path.join(dbdir, db_hash_dir), "%s.json" % hash)
			metadata = load_metadata(metadatapath)
			
			exts = [os.path.splitext(f)[1] for f in metadata["filenames"]]
			image_hashes = {}
			for f,ext in zip(metadata["filenames"], exts):
				if ext in IMAGE_EXTENSIONS:
					hash_filepath = os.path.join(os.path.join(dbdir, db_hash_dir), "%s%s" % (hash,ext))
					image_hash = compute_image_hash(hash_filepath, ext)
					image_hashes[f] = image_hash
				progress_bar.update(1)
			metadata["image_hashes"] = image_hashes
			write_content_metadata(metadatapath, metadata)
		progress_bar.update(1) # update for subdirectory count from glob total

### BARD INPUTS:
def parse_bard_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--importdir", type=str, help="import directory")
	parser.add_argument("-d", "--databasedir", type=str, help="database (.bard) directory")
	parser.add_argument("-m", "--mountdir", type=str, help="create symlink directory structure pointing to bard files")
	parser.add_argument("-f", "--fingerprint", help="compute and store image content hashes to metadata json in bard imported files")
	args = parser.parse_args()

	mountdir = ''
	if not(args.mountdir is None):
		mountdir = args.mountdir

	fingerprint = False
	if not(args.fingerprint is None):
		fingerprint = True

	importdir = None
	if (args.importdir is None) and (mountdir == '') and (not fingerprint):
		print("Error! import directory required!")
		import sys
		sys.exit()
	if not (args.importdir is None):
		importdir = os.path.abspath(args.importdir)

	dbdir = '.bard'
	if not(args.databasedir is None):
		dbdir = args.databasedir
	return importdir,dbdir,mountdir,fingerprint

# Future Feature Ideas:
# Threading w/subprocess
# Tag inserts to metadata json
# rolling hash for large files like rsync
# import archives
# Windows
# handle b2sum missing on OS
# Note: might want to delete OLD version, clear OLD modtime version.  Maybe add a "clean" function?
# Note: same content hash with different image extension i.e. jpg vs. png. Might want to only have one version.

# Usage: python3 bard.py -i <folder_path>
# import example: python3 bard.py -i <path_to_directory_to_import>
# mount example: python3 bard.py -m <local symlink directory to imported bard>
# fingerprint example: python3 bard.py -f <1, true, some dummy arg here to indicate do it>
# fingerprint runs image content hash on all bard images and records in metadata json.
# Can always optionally specify .bard directory with -d
if __name__ == "__main__":
	importdir,dbdir,mountdir,fingerprint = parse_bard_args()

	dbmoddir = os.path.join(dbdir, MODDIR)
	if not (os.path.exists(dbdir)):
		os.makedirs(dbdir)
		os.makedirs(dbmoddir)

	if (not (importdir is None) and (mountdir == "")):
		import_db_dir(importdir)
	elif not (mountdir == ""):
		create_symlink_file_tree_from_db(mountdir, dbdir)
	elif(fingerprint):
		do_fingerprint(dbdir)





########## METADATA EXTENSIONS


def compute_image_hash(f, ext):
# filetypes that aren't images for future consideration:
# vector: .svg (technically an image type but not pixelized for image hash)
# videos: .mp4, .webm
# plaintext: .txt, .csv, .yaml/.yml, .xml, .json, .conf
# compiled text: .pdf,
# code: .kdev*, .cpp, .h, .hpp, .c, .cc, .py, .sh, .bat, .m, Makefile/README(.md, .rst), CMakeLists.txt, .git
# documents: .odt, .xls, .xlxs, .doc, .docx, 
# latex: .tex, .bib, .aux, .bbl, .bst, .sty
# web: .html, .css, .php, 
# types that probably shouldn't be hashed: (.o, .pyc, .a, .so*, .obj)
# linked exe: .bin, .exe
# pem: .pem
# keys: .gpg, .pub
# disk images: .iso
# archives: .tar, .tar.gz, .tgz, .zip, .h5
	if (ext in IMAGE_EXTENSIONS):
		img = Image.open(f)
		hash = imagehash.dhash(img)
		hash = "%s" % hash
		return hash
	else:
		print("not an image!")
		return 0




