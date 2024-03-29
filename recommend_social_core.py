import json
from pymongo import MongoClient


client = MongoClient()
db = client['gtr']


def sort_to_k(ary,k,key=lambda x:x,reversed=False):
    k = min(k,len(ary))
    for i in range(k):
        for j in range(len(ary)-1-i):
            if not reversed:
                if key(ary[len(ary)-1-j]) < key(ary[len(ary)-2-j]):
                    ary[len(ary)-1-j],ary[len(ary)-2-j] = ary[len(ary)-2-j],ary[len(ary)-1-j]
            else:
                if key(ary[len(ary)-1-j]) > key(ary[len(ary)-2-j]):
                    ary[len(ary)-1-j],ary[len(ary)-2-j] = ary[len(ary)-2-j],ary[len(ary)-1-j]
    return ary


graph = []
node_ind = {}
with open("network.json") as nj:
    j = json.load(nj)
    nodes = j['nodes']
    for i,node in enumerate(nodes):
        node_ind[node] = i
        graph.append({})
    aware = j['aware']
    for u1,g in enumerate(aware):
        for u in g:
            u2 = int(u)
            if not u2 in graph[u1]:
                graph[u1][u2] = 0
            if not u1 in graph[u2]:
                graph[u2][u1] = 0
            graph[u1][u2] += len(g[u])
            graph[u2][u1] += len(g[u])


team_profiles = db['team_profiles']
user_teams = {}
for t_p in team_profiles.find():
    for user in json.loads(t_p['team']):
        if not user in user_teams:
            user_teams[user] = []
        user_teams[user].append(t_p['team'])


repo_core_targets = db['repo_core_targets']
cnt = 0
ks = [5,10,30,50]
files = [open("recommend_social_%d.json"%k,'w') for k in ks]
for r_ct in repo_core_targets.find():
    if cnt < 62546:
        cnt += 1
        continue
    print(cnt)
    team_score = {}
    for user in r_ct['core_users']:
        if not user in node_ind:
            continue
        for u2 in graph[node_ind[user]]:
            if not nodes[u2] in user_teams:
                continue
            for tm in user_teams[nodes[u2]]:
                if tm in r_ct['core_teams']:
                    continue
                if not tm in team_score:
                    team_score[tm] = 0
                team_score[tm] += graph[node_ind[user]][u2]
    tms = sort_to_k(list(team_score),ks[-1],key=lambda i:team_score[i],reversed=True)
    for ii,k in enumerate(ks):
        files[ii].write(r_ct['repo'])
        for i in range(min(k,len(tms))):
            files[ii].write('\t'+json.dumps((tms[i],team_score[tms[i]])))
        files[ii].write("\n")
    cnt += 1