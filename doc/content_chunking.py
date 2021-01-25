import hashlib
import os,os.path
import subprocess
import tempfile
import platform

def make_randoms(num_bits=64):
	out=[]
	for i in range(256):
		hsh=hashlib.blake2b(b"CONTENT_CHUNK",digest_size=num_bits//8,key=bytes(32*[i])).hexdigest()
		hshv=int(hsh,16)
		out.append(hshv)
	return out


hlen=64
bytetable=make_randoms(hlen)
btmax=1 << hlen

def chunkify(biter,chunk_target):
	currbytes=bytearray()
	curhash=0
	#k=chunk_target #why does this emperically converge on 1.25? (1255?)) ((1.25349))
	#sqrt(phi?)
	#k=(chunk_target*4)//5
	k=int(float(chunk_target)/1.25)
	kk=k*k
	
	rollbuffer=[0]*hlen
	
	#k is an power of 2 where the probability of success is 1/k
	Z=(1<<hlen)
	H=hlen-1
	K=(Z-1)//kk
	T=0

	for b in biter:
		tail=rollbuffer[len(currbytes) & H]
		curhash ^= tail
		bv=bytetable[b]
		rollbuffer[len(currbytes) & H]=bv
		curhash = (((curhash << 1) | curhash >> (hlen-1)) ^ bv) & (btmax-1)
		currbytes.append(b)
		T+=K				#in C version check for overflow of T
		if(curhash < T):
			curhash=0
			yield currbytes
			currbytes=bytearray()
			rollbuffer=[0]*hlen
			T=0

def serialize_bytetable():
	sout=""
	for i,b in enumerate(bytetable):
		sout+="0x%016x," %(b)
		if(i%8 == 7):
			sout+="\n"
	return sout.strip().strip(',')


def _get_bin_suffix():
	if(platform.system()=="Windows"):
		return '.exe'
	else:
		return ''

def _tmpfile(suffix,text):
	with tempfile.mkstemp(suffix=suffix,text=text) as z:
		os.close(z[0])
		return z[1]

def _compile():
	try:
		dir_path = os.path.dirname(os.path.realpath(__file__))
		chunkify_c = os.path.join(dir_path,'chunkify.c')
		print(chunkify_c)
		chunkify_exe=_tmpfile('-chunkify'+_get_bin_suffix(),text=False)
		bytetable_c = _tmpfile('.c',text=True)

		with open(bytetable_c,"w+") as bytetablefile:
			bytetablefile.write("#include<stdint.h>\nconst uint64_t bytetable[64]={\n"+serialize_bytetable()+"\n};")
		result=subprocess.run(["cc",chunkify_c,bytetable_c,"-o",chunkify_exe,"-O2"],check=True)
		os.unlink(bytetable_c)
		return chunkify_exe
	except Exception as e:
		print("Warning: compiling fast content chunker failed. You might need to install a compiler.")
		print(e)
		return None

def _get_compiled_chunkify_exe():
	dir_path = os.path.dirname(os.path.realpath(__file__))
	tempdir=tempfile.gettempdir()
	chunkify_exe=os.path.join(tempdir,"chunkify"+_get_bin_suffix())
	if(not os.path.exists(chunkify_exe)):
		tmp_exe=_compile()
		if(tmp_exe==None):
			return None
		else:		
			os.replace(tmp_exe,chunkify_exe)
	return chunkify_exe


_binary=_get_compiled_chunkify_exe()


if __name__=="__main__":
	import random
	import secrets
	import matplotlib.pyplot as plt
	import time

	def run_test(allbytes,k=2048):
		t0=time.time()
		results=[len(c) for c in chunkify(allbytes,k)]
		t1=time.time()-t0
		u=float(sum(results))/len(results)
		rate=len(allbytes)/t1
		return results,u,rate

	def estimate_and_test1():
		N=1 << 27
		print("Generating testbytes")
		allbytes=secrets.token_bytes(N)
		#allbytes=[random.randint(0,255) for _ in range(N)]
		print("Running chunks")
		results,u,rate=run_test(allbytes,2048)		
		print("Mean: "+str(u))
		print("Rate: "+str(rate))
		plt.hist(results,bins=128)
		plt.show()

	def mean_center():
		N=1 << 26
		#print("Generating testbytes")
		allbytes=secrets.token_bytes(N)
		for i in range(1):
			for lk in range(10,20):
				k=1 << lk
				#print("Running chunks: %d" % k)
				results,u,rate=run_test(allbytes,k)		
				print("%d,%f" % (k,u))
				#print("Rate: "+str(rate))
	
	#mean_center()
	#estimate_and_test1()
	#plt.hist(results,bins=128)
	#plt.show()
	#print(serialize_bytetable())
