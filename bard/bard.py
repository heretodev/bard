import json
import os
import shutil
import datetime
import argparse
import math
import shutil
import bard.hash

#optional stuff

#from pathlib import Path # Python3.5 onward (for progress bar in import)
#from tqdm import tqdm # progress bar
#TODO:   Confirm that if a file into the bitwise is interrupted that the corrupted entry is not written.
#TODO: allow tqdm on import optional otherwise fallback.
#TODO: allow threading iff filelock is enabled.



### METADATA FUNCTIONS: ONE UNIQUE PER data HASH
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
	#bug here 
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



def import_db_dir(dbdir,importdir, progress_bar = None, total_files = 0, display_recursive_progress = True):
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
		progress_bar = import_db_dir(dbdir,d, progress_bar, total_files)
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

def create_symlink_file_tree_from_db(dbdir, mount):
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

def do_fingerprint(dbdir,types):
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

	









