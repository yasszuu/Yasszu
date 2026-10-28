import json, shapefile, os
r = shapefile.Reader('../animal/ne/ne_10m_admin_0_map_units.shp'); f = [x[0] for x in r.fields[1:]]
rows = [(dict(zip(f, s.record)), s.shape) for s in r.iterShapeRecords()]
def parts(sh):
    p = sh.points; idx = list(sh.parts) + [len(p)]; return [p[idx[i]:idx[i+1]] for i in range(len(idx) - 1)]
def area(q): return abs(sum(q[i][0]*q[i+1][1] - q[i+1][0]*q[i][1] for i in range(len(q) - 1)))/2
def rings(sh, minA, step=1, lonr=(-180, 180)):
    o = []
    for q in parts(sh):
        xs = [p[0] for p in q]
        if max(xs) - min(xs) > 180 or area(q) < minA or min(xs) < lonr[0] or max(xs) > lonr[1]: continue
        o.append([[round(a, 3), round(b, 3)] for a, b in q[::step] + [q[0]]])
    return o
U = {d['GEOUNIT']: s for d, s in rows}

G = {'POL': rings(U['Poland'], 0.01), 'IRN': rings(U['Iran'], 0.02, 2), 'IRQ': rings(U['Iraq'], 0.01, 2), 'SYR': rings(U['Syria'], 0.01, 2), 'PAL': rings(U['Israel'], 0.002) + rings(U['West Bank'], 0.002) + rings(U['Gaza'], 0.0005), 'EGY': rings(U['Egypt'], 0.02, 2), 'ITA': rings(U['Italy'], 0.01), 'SCT': rings(U['Scotland'], 0.01)}
B = []
for d, s in rows: B += rings(s, 0.15, 3)
json.dump({'c': G, 'b': B}, open('geo.json', 'w'), separators=(',', ':'))
print({k: (len(v), sum(map(len, v))) for k, v in G.items()}, len(B), os.path.getsize('geo.json'))
