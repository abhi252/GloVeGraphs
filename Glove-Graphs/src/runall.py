import os
import numpy as np 

for j in np.arange(0.3,1,0.1):
	path = '../data/mu_'+str(j)+'_N_1000/'
	for i in range(1,6):
		ip = path + 'network_run_'+str(i)+'.dat'
		op = path + 'embedding_run_'+str(i)+'.emb'
		cmd = 'python runner.py --input '+ip+' --output '+op+' --iterations 200 --learning-rate 0.01'
		print cmd
		os.system(cmd)