import os

d = "."

subdirs = [x[0] for x in os.walk(d)]

lists = ["testing", "validation",]
items_per_part = [10,10]

DEBUG = 1
if DEBUG:
    subdirs = ["hey_hal", "play"]


example_lists = {}

for k, l in enumerate(lists):
    l_ = []
    for sd in subdirs:
        examples = os.listdir(sd)
        for example in examples:
            numeric = int(example.split(".")[0])
            if sum(items_per_part[:k]) <= numeric <= sum(items_per_part[:k+1]):
                l_.append(os.path.join(sd, example)+"\n")
    example_lists[l] = l_

ext = "_list.txt"
for l in lists:
    with open(l+ext, "w") as TXT:
        TXT.writelines(example_lists[l])


