"""Année (approximative) d'implantation du moustique tigre par département.
Calée sur les jalons publiés : 06 en 2004, 2B 2006, 2A+83 2007, 04+13 2010, 30+34+84 2011,
20 départements fin 2014, Val-de-Marne 2015, Paris 2018, 51 début 2019, 71 en 2022, 78 en 2023,
81 au 1er janvier 2025 (Marne, Haute-Marne, Haute-Saône en 2024). Non colonisés au 01/01/2025 : None."""
import json
Y = {}
def put(y, codes):
    for c in codes.split(): Y[c] = y
put(2004, "06"); put(2006, "2B"); put(2007, "2A 83"); put(2010, "04 13"); put(2011, "30 34 84")
put(2012, "11 66 26 07 69 38 47 31"); put(2013, "33"); put(2014, "73 01")
put(2015, "94 74 64 40 24 46 09 81 12 65"); put(2016, "42 71 63")
put(2017, "82 32 05 92 93 15 43 03 21"); put(2018, "75 91 17 16 86 19 87 39 48")
put(2019, "78 95 77 79 85 44 49"); put(2020, "37 41 45 18 36 58 53"); put(2021, "89 25 68 67")
put(2022, "54 57"); put(2023, "72 88 90 56 35 60 27"); put(2024, "51 52 70")
NONE = "23 50 29 08 59 14 22 10 28 61 76 62 80 02 55".split()
d = json.load(open("../dep.geojson"))
codes = [f["properties"]["code"] for f in d["features"]]
miss = [c for c in codes if c not in Y and c not in NONE]
assert not miss, miss
from collections import Counter
cum, n = {}, 0
for y in sorted(set(Y.values())): n += Counter(Y.values())[y]; cum[y] = n
print(cum, len(NONE))
json.dump({c: Y.get(c) for c in codes}, open("dep_years.json", "w"))
