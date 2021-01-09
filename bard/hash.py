import subprocess
import binascii
import base64
import hashlib


HASH_SUBDIR_LEN = 3
MODHASH_SUBDIR_LEN = 3
MODDIR = "mod"
SECURE_HASH_LEN=256

def _secure_hash_filepath_shell(filepath):
	completed_process = subprocess.run(["b2sum", "-l", str(SECURE_HASH_LEN), "-b", filepath], capture_output=True)
	completed_process.check_returncode()
			
	line=completed_process.stdout
	if(len(line) < (2*SECURE_HASH_LEN//8)):
		return _secure_hash_filepath_py3(filepath)
	else:
		hsh=binascii.unhexlify(line[0:64])
		base64.b32encode(hsh).decode("ascii")

def _secure_hash_filepath_py3(filepath):
	with open(filepath,'rb') as fo:
		gfg = hashlib.blake2b() # need to create fresh for each hash
		while True:
			data = file_object.read(chunk_size)
			if not data:
				break
			gfg.update(s)
		return base64.b32encode(gfg.digest()).decode("ascii")

secure_hash_filepath=_secure_hash_filepath_shell

if(subprocess.run(["b2sum", "-l", str(SECURE_HASH_LEN), "-b", __file__], capture_output=True).returncode < 0):
	secure_hash_filepath=_secure_hash_filepath_py3

def secure_hash(s):
	gfg = hashlib.blake2b() # need to create fresh for each hash
	gfg.update(s)
	hash = gfg.digest()
	return base64.b32encode(hash).decode("ascii")
