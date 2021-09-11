import json
import sys


tmp = "tmp/last_query.json"

with open(tmp, "r") as myfile:
    data=myfile.read()

results = json.loads(data)

ids=[]
for r in results["items"]:
    videoId = r["id"]["videoId"]
    ids.append(videoId)

for r in reversed(ids):
    print(r)
    



    
    
