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

except ImportError as ie:
	warnings.warn("PIL and imagehash are required to do image fingerprinting.  image fingerprinting will not be enabled")



