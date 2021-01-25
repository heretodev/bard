import warnings

try:
	from PIL import Image
	import imagehash

	IMAGE_EXTENSIONS = [".jpg", ".png", ".jpeg", ".bmp", ".pgm", ".ppm", ".tiff"]


	def compute_image_fingerprint(f, ext):
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
			hsh = imagehash.dhash(img)
			hsh = "%s" % hsh
			return hsh
		else:
			return None

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


except ImportError as ie:
	warnings.warn("PIL and imagehash are required to do image fingerprinting.  image fingerprinting will not be enabled")



