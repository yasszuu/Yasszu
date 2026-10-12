const fs=require('fs'), b64=p=>fs.readFileSync(p).toString('base64');
const dep=JSON.parse(fs.readFileSync('dep.geojson'));
// arrondi des coordonnées pour alléger
const r=a=>typeof a[0]==='number'?[+a[0].toFixed(4),+a[1].toFixed(4)]:a.map(r);
dep.features.forEach(f=>f.geometry.coordinates=r(f.geometry.coordinates));
let s=fs.readFileSync('src.html','utf8');
const rep={__ANTON__:b64('node_modules/@fontsource/anton/files/anton-latin-400-normal.woff2'),
 __INTER400__:b64('node_modules/@fontsource/inter/files/inter-latin-400-normal.woff2'),
 __INTER700__:b64('node_modules/@fontsource/inter/files/inter-latin-700-normal.woff2'),
 __D3__:fs.readFileSync('node_modules/d3/dist/d3.min.js','utf8'),
 __TOPOJSON__:fs.readFileSync('node_modules/topojson-client/dist/topojson-client.min.js','utf8'),
 __WORLD__:fs.readFileSync('node_modules/world-atlas/countries-50m.json','utf8'),
 __DEPS__:JSON.stringify(dep)};
for(const[k,v]of Object.entries(rep)) s=s.split(k).join(v);
fs.writeFileSync('carte-delinquance.html',s); console.log((s.length/1e6).toFixed(2)+' MB');
