import os
import sys
import json
import subprocess

compmap_json = sys.argv[1]
parts_folder = sys.argv[2]
images_folder = sys.argv[3]

fs = os.listdir(images_folder)
for f in fs:
    os.unlink(os.path.join(images_folder, f))

compmap = {}
with open(compmap_json) as f:
    jd = json.load(f)
    for p in jd:
        pg = jd[p]
        if not pg in compmap:
            compmap[pg] = []
        compmap[pg].append(p)

for pg in compmap:
    compmap[pg].sort(key=lambda x:(len(x), x))

for pg in compmap:
    ps = []
    print(pg)
    for p in compmap[pg]:
        pf = os.path.join(parts_folder, p+".jpg")
        if os.path.exists(pf):
            ps.append(pf)
        else:
            print("\tSkip", p)
    if ps:
        gif = pg+".gif"
        subprocess.call(["convert", "-loop", "0", "-delay", "50"]+ps+[os.path.join(images_folder, gif)])
