	import random
	import matplotlib.pyplot as plt

	def sample_one(k,scale=1.0):
		q=k*scale
		K=1.0/(q*q)
		count=0
		T=0
		while(random.random() >= T):
			T=K*count
			count+=1
		return count	

	def get_distribution(N=100000,k=2048):
		results=[sample_one(k) for _ in range(N)]
		plt.hist(results,bins=256)
		plt.show()

	get_distribution()
