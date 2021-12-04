import json
import sys

relative_dir = "scripts/"

tmp = relative_dir + "tmp/last_query.json"

with open(tmp, "r") as myfile:
    data=myfile.read()

results = json.loads(data)

ids=[]
# print("results:", results)
for r in results["items"]:
    videoId = r["id"]["videoId"]
    ids.append(videoId)

# for piping
for r in reversed(ids):
    print(r)

