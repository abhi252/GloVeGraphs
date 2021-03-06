import numpy as np
import networkx as nx
import random

import msgpack
from collections import defaultdict

class NodeCooccur():
	def __init__(self, nx_G, p, q, weighted):
		self.G = nx_G
		self.p = p
		self.q = q
		self.weighted = weighted
		self.node_map,self.rev_map = self.gen_node_map()
		#self.preprocess_transition_probs()

	def get_node_map(self):
		return self.node_map

	def gen_node_map(self):
		G = self.G
		nodes = sorted(list(G.nodes()))
		node_map = {}
		rev_map = {}
		ctr = 0
		for n in nodes:
			node_map[ctr] = n
			rev_map[n] = ctr
			ctr += 1
		return node_map,rev_map

	def simulate_walk(self, walk_length, start_node) :
		G = self.G
		alias_nodes = self.alias_nodes
		alias_edges = self.alias_edges

		walk = [start_node]

		while len(walk) < walk_length:
			cur = walk[-1]
			cur_nbrs = sorted(G.neighbors(cur))
			if len(cur_nbrs) > 0:
				if len(walk) == 1:
					walk.append(cur_nbrs[alias_draw(alias_nodes[cur][0], alias_nodes[cur][1])])
				else:
					prev = walk[-2]
					next = cur_nbrs[alias_draw(alias_edges[(prev, cur)][0], 
						alias_edges[(prev, cur)][1])]
					walk.append(next)
			else:
				break

		return walk

	def build_cooccurence(self, num_walks, walk_length):
		G = self.G
		'''walks = []
		cooccur = []
		occurDict = defaultdict(int)
		nodes = list(G.nodes())
		min_label = min(nodes)
		print 'Walk iteration:'
		for walk_iter in range(num_walks):
			print str(walk_iter+1), '/', str(num_walks)
			random.shuffle(nodes)
			for node in nodes:
				walk = self.simulate_walk(walk_length=walk_length, start_node=node)
				walks.append(walk)
				for n in walk:
					if n != node:
						occurDict[str(node)+'-'+str(n)] += 1
						occurDict[str(n)+'-'+str(node)] += 1
		for key in occurDict:
			a = key.split('-')
			cooccur.append((int(a[0])-min_label,int(a[1])-min_label,occurDict[key]))
	
		# with open('../glove.py-master/lesmis-cooccur', 'wb') as obj_f:
		# 	msgpack.dump(cooccur,obj_f)
		return cooccur'''
		if self.weighted:
			res = nx.shortest_path(G)
		else:
			res = nx.shortest_path_length(G)
		dist_cooccur = []
		for src in res:
		    for dest in res[src]:
		        if src != dest:
		        	m_src = self.rev_map[src]
		        	m_dest = self.rev_map[dest]
		        	#print 'accessing src : ',src,' dest : ',dest
		        	if self.weighted:
		        		path = res[src][dest]
		        		if len(path) > 5:
		        			continue
		        		l = 0
		        		for i in range(len(path) -1):
		        			l += G[path[i]][path[i+1]]['weight']
		        		dist_cooccur.append((m_src, m_dest, 1.0/l))
		        	else:
		        		dist_cooccur.append((m_src, m_dest, 1.0/(res[src][dest])))
		return dist_cooccur

	def get_alias_edge(self, src, dst):
		G = self.G
		p = self.p
		q = self.q

		unnormalized_probs = []
		for dst_nbr in sorted(G.neighbors(dst)):
			if dst_nbr == src:
				unnormalized_probs.append(G[dst][dst_nbr]['weight']/p)
			elif G.has_edge(dst_nbr, src):
				unnormalized_probs.append(G[dst][dst_nbr]['weight'])
			else:
				unnormalized_probs.append(G[dst][dst_nbr]['weight']/q)
		norm_const = sum(unnormalized_probs)
		normalized_probs =  [float(u_prob)/norm_const for u_prob in unnormalized_probs]

		return alias_setup(normalized_probs)

	def preprocess_transition_probs(self):
		G = self.G

		alias_nodes = {}
		for node in G.nodes():
			unnormalized_probs = [G[node][nbr]['weight'] for nbr in sorted(G.neighbors(node))]
			norm_const = sum(unnormalized_probs)
			normalized_probs =  [float(u_prob)/norm_const for u_prob in unnormalized_probs]
			alias_nodes[node] = alias_setup(normalized_probs)

		alias_edges = {}
		triads = {}
		for edge in G.edges():
			alias_edges[edge] = self.get_alias_edge(edge[0], edge[1])
			alias_edges[(edge[1], edge[0])] = self.get_alias_edge(edge[1], edge[0])

		self.alias_nodes = alias_nodes
		self.alias_edges = alias_edges

		return


def alias_setup(probs):
	'''
	Compute utility lists for non-uniform sampling from discrete distributions.
	Refer to https://hips.seas.harvard.edu/blog/2013/03/03/the-alias-method-efficient-sampling-with-many-discrete-outcomes/
	for details
	'''
	K = len(probs)
	q = np.zeros(K)
	J = np.zeros(K, dtype=np.int)

	smaller = []
	larger = []
	for kk, prob in enumerate(probs):
	    q[kk] = K*prob
	    if q[kk] < 1.0:
	        smaller.append(kk)
	    else:
	        larger.append(kk)

	while len(smaller) > 0 and len(larger) > 0:
	    small = smaller.pop()
	    large = larger.pop()

	    J[small] = large
	    q[large] = q[large] + q[small] - 1.0
	    if q[large] < 1.0:
	        smaller.append(large)
	    else:
	        larger.append(large)

	return J, q

def alias_draw(J, q):
	K = len(J)

	kk = int(np.floor(np.random.rand()*K))
	if np.random.rand() < q[kk]:
	    return kk
	else:
	    return J[kk]