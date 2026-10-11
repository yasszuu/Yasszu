import json, shapefile, os, subprocess
r = shapefile.Reader('../animal/ne/ne_10m_admin_0_map_units.shp'); f = [x[0] for x in r.fields[1:]]
rows = [(dict(zip(f, s.record)), s.shape) for s in r.iterShapeRecords()]
def parts(sh):
    p = sh.points; idx = list(sh.parts) + [len(p)]; return [p[idx[i]:idx[i+1]] for i in range(len(idx) - 1)]
def area(q): return abs(sum(q[i][0]*q[i+1][1] - q[i+1][0]*q[i][1] for i in range(len(q) - 1)))/2
def rings(sh, minA, lonmin=-180, lonmax=180):
    o = []
    for q in parts(sh):
        xs = [p[0] for p in q]
        if max(xs) - min(xs) > 180 or min(xs) < lonmin or max(xs) > lonmax or area(q) < minA: continue
        o.append([[round(a, 3), round(b, 3)] for a, b in q])
    return o
U = {d['GEOUNIT']: s for d, s in rows}
G = {'FRA': rings(U['France'], 0.01, -6, 10), 'ITA': rings(U['Italy'], 0.01)}
B = []
for d, s in rows: B += rings(s, 0.08)
D = {}
for ft in json.load(open('../dep.geojson'))['features']:
    g = ft['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    rs = []
    for p in polys:
        q = p[0]
        if area(q) < 0.002: continue
        rs.append([[round(a, 3), round(b, 3)] for a, b in q[::2] + [q[0]]])
    D[ft['properties']['code']] = rs
json.dump({'c': G, 'b': B, 'd': D}, open('geo.json', 'w'), separators=(',', ':'))
os.makedirs('flags', exist_ok=True)
for c in ['fr', 'it', 'eu']: subprocess.run(['cp', f"../animal/pkg/package/flags/4x3/{c}.svg", 'flags/'])
print({k: len(v) for k, v in G.items()}, len(B), len(D), os.path.getsize('geo.json'))
