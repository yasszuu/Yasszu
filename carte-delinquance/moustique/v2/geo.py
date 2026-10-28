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
us = rings(U['United States of America'], 0.05, 3); us = [max(us, key=len)]
G = {'FRA': rings(U['France'], 0.01, 1, (-6, 10)), 'ITA': rings(U['Italy'], 0.01), 'ALB': rings(U['Albania'], 0.001), 'USA': us}
B = []
for d, s in rows: B += rings(s, 0.15, 3)
D = {}
for ft in json.load(open('../dep.geojson'))['features']:
    g = ft['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    D[ft['properties']['code']] = [[[round(a, 3), round(b, 3)] for a, b in p[0][::2] + [p[0][0]]] for p in polys if area(p[0]) >= 0.002]
json.dump({'c': G, 'b': B, 'd': D}, open('geo.json', 'w'), separators=(',', ':'))
print({k: (len(v), sum(map(len, v))) for k, v in G.items()}, len(B), len(D), os.path.getsize('geo.json'))
