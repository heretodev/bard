import time
import hashlib
import secrets

def run_experiment(hsh,iters=1000,size=1<<26):
	allbytes=secrets.token_bytes(size)
	print(dir(hsh))
	t=time.perf_counter() 
	for i,_ in enumerate(allbytes):
		hsh.update(allbytes[i:(i+1)])
		d=hsh.digest()
	print(time.perf_counter()-t)
	print(hsh.hexdigest())
	print(hashlib.blake2s(allbytes).hexdigest())


run_experiment(hashlib.blake2s())	
