import sys, os, itertools
site_packages=[p for p in sys.path if 'site-packages' in (p or '')]
seen=set(); cnt=0
for sp in itertools.islice(site_packages,0,10):
    try:
        for root, dirs, files in os.walk(sp):
            for name in files:
                if 'onnxruntime' in name.lower():
                    path=os.path.join(root,name)
                    if path not in seen and cnt<200:
                        print(path)
                        seen.add(path); cnt+=1
    except Exception:
        pass
print('done')
