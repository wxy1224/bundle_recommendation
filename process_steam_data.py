import json
from pprint import pprint
import ast
import snap
import sys
import time
import pickle
import csv

# >600000

def save_obj(obj, name ):
    with open('graph/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open('graph/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

''' not in use '''
def generate_game_dict(checkpoint=0):
	FIn = snap.TFIn("graph/steam.graph")
	G = snap.TUNGraph.Load(FIn)

	

	user_node_array = [] #88310
	with open('graph/user_node.txt', 'r') as f:
	    for line in f:
	        user_node_array.append(int(line))

	game_node_array = [] #10978
	with open('graph/game_node.txt', 'r') as f:
	    for line in f:
	        game_node_array.append(int(line)) 

	game_dict = {}

	print("start game dict")

	count = 0
	for nid in user_node_array:
		start = time.time()
		if count<checkpoint:
			count+=1
			continue
		node = G.GetNI(nid)
		ki = node.GetDeg()
		neid = []
		for i in range(ki):
			neid.append(node.GetNbrNId(i))
		for i in range(len(neid)):
			for j in range(i+1,len(neid)):
				if (neid[i], neid[j]) in game_dict.keys():
					game_dict[(neid[i], neid[j])]+=1
				else:
					game_dict[(neid[i], neid[j])]=1

		count+=1
		print(count, ki, len(game_dict.keys()), time.time()-start)
		# if count%10==0:
		# 	print(count, len(game_dict.keys()), "percentage: %f" % (count/float(len(user_node_array))))
		# if count%100==0:
		# 	print("time", len(game_dict.keys()), time.time()-start)
	save_obj(game_dict, 'game_dict')


''' bipartite graph '''
def generate_steam_graph():
	G = snap.TUNGraph.New()
	user_node_array = []
	user_node_id = 600000
	game_node_array = [] #10978
	# min_game_id = sys.maxint #10
	# max_game_id = 0 #530720
	# count1=0
	# count2=0
	with open("data/australian_users_items.json") as f:
		for line in f:
			data = ast.literal_eval(line)
			user_id = data['user_id']
			item_count = int(data['items_count'])
			# if item_count>900:
			# 	count1+=1
			# if item_count>1000:
			# 	count2+=1
			G.AddNode(user_node_id)
			items = data['items']
			for item in items:
				item_id = int(item['item_id'])
				# min_game_id = min(item_id, min_game_id)
				# max_game_id = max(item_id, max_game_id)
				if not G.IsNode(item_id):
					G.AddNode(item_id)
					game_node_array.append(item_id)
				G.AddEdge(user_node_id, item_id)
			user_node_array.append(user_node_id)
			user_node_id+=1
	# print(len(game_node_array))
	# print(min_game_id, max_game_id)
	with open('graph/user_node.txt', 'w') as f:
	    for item in user_node_array:
	        f.write("%d\n" % item)

	with open('graph/game_node.txt', 'w') as f:
	    for item in game_node_array:
	        f.write("%d\n" % item)

	FOut = snap.TFOut("graph/steam.graph")
	G.Save(FOut)
	FOut.Flush()

def generate_steam_game_graph():
	FIn = snap.TFIn("graph/steam.graph")
	G = snap.TUNGraph.Load(FIn)

	user_node_array = [] #88310
	with open('graph/user_node.txt', 'r') as f:
	    for line in f:
	        user_node_array.append(int(line))

	game_node_array = [] #10978
	with open('graph/game_node.txt', 'r') as f:
	    for line in f:
	        game_node_array.append(int(line)) 

	G_game = snap.TUNGraph.New()
	# add nodes
	for uid in game_node_array:
		G_game.AddNode(uid)
	# add edges
	count=0
	for node in G.Nodes():
		NId = node.GetId() 
		if NId in user_node_array:
			ki = node.GetDeg()
			neid = []
			for i in range(ki):
				neid.append(node.GetNbrNId(i))
			for i in range(len(neid)):
				for j in range(i+1,len(neid)):
					G_game.AddEdge(neid[i], neid[j])
		count+=1
		if count%1000==0:
			print("percentage: %f" % (count/(float(G.GetNodes()))))
	FOut = snap.TFOut("graph/steam_game.graph")
	G_game.Save(FOut)
	FOut.Flush()

	FIn = snap.TFIn("graph/steam_game.graph")
	G_game = snap.TUNGraph.Load(FIn)
	ClustCf = snap.GetClustCf(G_game, 1000)
	print("clustering coefficient: %f" % ClustCf)
	return G_game


''' generate steam game weight graph previous'''

def generate_steam_game_weight_graph(limit):
	FIn = snap.TFIn("graph/steam.graph")
	G = snap.TUNGraph.Load(FIn)

	user_node_array = [] #88310
	with open('graph/user_node.txt', 'r') as f:
	    for line in f:
	        user_node_array.append(int(line))

	game_node_array = [] #10978
	with open('graph/game_node.txt', 'r') as f:
	    for line in f:
	        game_node_array.append(int(line)) 

	G_game = snap.TNEANet.New()
	attr = 'weight'
	# add nodes
	for uid in game_node_array:
		G_game.AddNode(uid)
	# add edges
	count=0
	for NId in user_node_array:
		node = G.GetNI(NId)
		ki = node.GetDeg()
		if ki>limit:
			count+=1
			continue
		neid = []
		for i in range(ki):
			neid.append(node.GetNbrNId(i))
		neid = sorted(neid)
		for i in range(len(neid)):
			for j in range(i+1,len(neid)):
				if G_game.IsEdge(neid[i], neid[j]):
					eid = G_game.GetEI(neid[i], neid[j]).GetId()
					value = G_game.GetIntAttrDatE(eid, attr)
					value+=1
					G_game.AddIntAttrDatE(eid, value, attr)
				else:
					eid = G_game.AddEdge(neid[i], neid[j])
					G_game.AddIntAttrDatE(eid, 1 , attr)	
		count+=1
		if count%1000==0:
			print(count, "percentage: %f" % (count/(float(len(user_node_array)))))
		if count%10000==0:
			FOut = snap.TFOut("graph/steam_weight_game_%d.graph"%count)
			G_game.Save(FOut)
			FOut.Flush()
			print("saved %d" % count)

	FOut = snap.TFOut("graph/steam_weight_game.graph")
	G_game.Save(FOut)
	FOut.Flush()
	print("done saving graph")

	FIn = snap.TFIn("graph/steam_weight_game.graph")
	G_game = snap.TNEANet.Load(FIn)
	ClustCf = snap.GetClustCf(G_game, 1000)
	print("clustering coefficient: %f" % ClustCf)
	return G_game

def save_edge_list(dct, name, count):
	with open('csv/new_steam_weight_{}_{}.csv'.format(name, str(count)), 'w') as f:
		writer = csv.writer(f, delimiter=',')
		for (id1, dct2) in dct.items():
			for (id2, value) in dct2.items():
				row = [str(id1), str(id2), str(value)]
				writer.writerow(row)

''' generate steam game user weight graph new'''
def generate_steam_game_user_weight_graph():
	FIn = snap.TFIn("../graph/steam_user100_game1000.graph")
	G = snap.TUNGraph.Load(FIn)

	# G_game = snap.PUNGraph.New()
	# G_user = snap.PUNGraph.New()
	game_dct = {}
	user_dct = {}
	# add edges
	count=0
	start = time.time()
	for node in G.Nodes():
		NId = node.GetId()
		if NId < 600000:			
			ki = node.GetDeg()
			neid = []
			for i in range(ki):
				neid.append(node.GetNbrNId(i))
			neid = sorted(neid)
			for i in range(len(neid)):
				for j in range(i+1,len(neid)):
					if neid[i] in user_dct:
						temp_dic = user_dct[neid[i]]
						if neid[j] in temp_dic:
							temp_dic[neid[j]]+=1
						else:
							temp_dic[neid[j]]=1
					else:
						user_dct[neid[i]] = {}
						user_dct[neid[i]][neid[j]]=1
			# print(user_dct)	
		else:
			ki = node.GetDeg()
			neid = []
			for i in range(ki):
				neid.append(node.GetNbrNId(i))
			neid = sorted(neid)
			for i in range(len(neid)):
				for j in range(i+1,len(neid)):
					if neid[i] in game_dct:
						temp_dic = game_dct[neid[i]]
						if neid[j] in temp_dic:
							temp_dic[neid[j]]+=1
						else:
							temp_dic[neid[j]]=1
					else:
						game_dct[neid[i]] = {}
						game_dct[neid[i]][neid[j]]=1
			# print(game_dct)
		# count+=1
		# if count%1000==0:
		# 	print(count, "percentage: %f" % (count/(float(G.GetNodes()))), time.time()-start)
		# if count%1000==0 or count==100:
		# 	save_edge_list(game_dct, 'game', count)
		# 	# save_edge_list(user_dct, 'user', count)
		# 	print("saved %d" % count)


	# FOut = snap.TFOut("graph/new_steam_weight_game.graph")
	# G_game.Save(FOut)
	# FOut.Flush()
	# FOut = snap.TFOut("graph/new_steam_weight_user.graph")
	# G_user.Save(FOut)
	# FOut.Flush()
	# print("done saving graph")
	# FIn = snap.TFIn("graph/new_steam_weight_game.graph")
	# G_game = snap.PUNGraph.Load(FIn)
	# ClustCf = snap.GetClustCf(G_game, 1000)
	# print("clustering coefficient: %f" % ClustCf)
	print len(game_dct), len(user_dct)
	# save_edge_list(game_dct, 'game', 0)
	# save_edge_list(user_dct, 'user', 0)
	return game_dct, user_dct

def generate_steam_edge_list():
	FIn = snap.TFIn("graph/steam_new.graph")
	G = snap.TUNGraph.Load(FIn)

	G = snap.GetMxWcc(G)

	user_node_array = [] #88310
	with open('graph/user_node.txt', 'r') as f:
	    for line in f:
	        user_node_array.append(int(line))

	game_node_array = [] #10978
	with open('graph/game_node.txt', 'r') as f:
	    for line in f:
	        game_node_array.append(int(line)) 

	with open('graph/steam_new_edge_list.csv', 'w') as f:
		writer = csv.writer(f, delimiter=',')
		for edge in G.Edges():
			# eid = edge.GetId()
			id1 = edge.GetSrcNId()
			id2 = edge.GetDstNId()
			if id1 in user_node_array:
				row = [str(id1), 'g'+str(id2)]
			else:
				row = [str(id2), 'g'+str(id1)]
			writer.writerow(row)


def generate_steam_user_weight_graph(limit):
	FIn = snap.TFIn("graph/steam.graph")
	G = snap.TUNGraph.Load(FIn)

	user_node_array = [] #88310
	with open('graph/user_node.txt', 'r') as f:
	    for line in f:
	        user_node_array.append(int(line))

	game_node_array = [] #10978
	with open('graph/game_node.txt', 'r') as f:
	    for line in f:
	        game_node_array.append(int(line)) 

	G_user = snap.TNEANet.New()
	attr = 'weight'
	# add nodes
	for uid in user_node_array:
		G_user.AddNode(uid)
	# add edges
	count=0
	for NId in game_node_array:
		node = G.GetNI(NId)
		ki = node.GetDeg()
		if ki>limit:
			count+=1
			continue
		neid = []
		for i in range(ki):
			neid.append(node.GetNbrNId(i))
		neid = sorted(neid)
		for i in range(len(neid)):
			for j in range(i+1,len(neid)):
				if G_user.IsEdge(neid[i], neid[j]):
					eid = G_user.GetEI(neid[i], neid[j]).GetId()
					value = G_user.GetIntAttrDatE(eid, attr)
					value+=1
					G_user.AddIntAttrDatE(eid, value, attr)
				else:
					eid = G_user.AddEdge(neid[i], neid[j])
					G_user.AddIntAttrDatE(eid, 1 , attr)	
		count+=1
		if count%1000==0:
			print(count, "percentage: %f" % (count/(float(len(game_node_array)))))
		if count%10000==0:
			FOut = snap.TFOut("graph/steam_weight_user_%d.graph"%count)
			G_user.Save(FOut)
			FOut.Flush()
			print("saved %d" % count)

	FOut = snap.TFOut("graph/steam_weight_user.graph")
	G_user.Save(FOut)
	FOut.Flush()
	print("done saving graph")

	FIn = snap.TFIn("graph/steam_weight_user.graph")
	G_user = snap.TNEANet.Load(FIn)
	ClustCf = snap.GetClustCf(G_user, 1000)
	print("clustering coefficient: %f" % ClustCf)
	return G_user



if __name__ == '__main__':
	# generate_steam_graph()
	# generate_steam_game_graph()
	# generate_steam_game_weight_graph(1000)
	# generate_steam_user_weight_graph(1000)
	# generate_steam_edge_list()
	generate_steam_game_user_weight_graph()
