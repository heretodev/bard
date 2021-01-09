import hashlib
import random
import math
import statistics

import matplotlib.pyplot as plt
import numpy as np

def make_randoms(num_bits=64):
	out=[]
	for i in range(256):
		hsh=hashlib.blake2b(b"CONTENT_CHUNK",digest_size=num_bits//8,key=bytes(32*[i])).hexdigest()
		hshv=int(hsh,16)
		out.append(hshv)
	return out


bytetable=make_randoms(64)

def chunkify(biter,chunk_target=2**16,difficulty_slope=1):
	difficulty=chunk_target
	difficulty_slope=int(difficulty_slope)
	currdifficulty=0
	currbytes=bytearray()
	curhash=0
	for b in biter:
		pass




def estimate_and_test():
	k=2**16
	#liklihood=0.99
	#p s.t. p^k=0.99   //means that 
	#geometric distribution
	#p^k (1-p)=liklihood
	#k log(p)+log(1-p)=liklihood
	# 
	i=0
	p=2**64
	kf=1.0/k
	while(random.random() > kf):
		kf=1.0/(k+i)
		i+=1
	return i

z=0
N=1000
results=[estimate_and_test() for x in range(N)]
plt.hist(results, bins=128)  # density=False would make counts
plt.show()
