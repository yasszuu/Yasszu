const fs=require('fs'), N='../../node_modules/', b64=p=>fs.readFileSync(p).toString('base64');
const imgs={}; for(const k of ['sterne','lune']) imgs[k]='data:image/png;base64,'+b64(k+'.png');
const rep={__M600__:b64(N+'@fontsource/montserrat/files/montserrat-latin-600-normal.woff2'),
 __M800__:b64(N+'@fontsource/montserrat/files/montserrat-latin-800-normal.woff2'),
 __M900__:b64(N+'@fontsource/montserrat/files/montserrat-latin-900-normal.woff2'),
 __D3__:fs.readFileSync(N+'d3/dist/d3.min.js','utf8'),
 __TOPOJSON__:fs.readFileSync(N+'topojson-client/dist/topojson-client.min.js','utf8'),
 __WORLD__:fs.readFileSync(N+'world-atlas/countries-50m.json','utf8'),
 __TL__:fs.readFileSync('timeline.json','utf8'), __IMGS__:JSON.stringify(imgs),
 __TEXWORLD__:'data:image/jpeg;base64,'+b64('tex_world.jpg'),
 __AUDIO__:fs.existsSync('mix.m4a')?'data:audio/mp4;base64,'+b64('mix.m4a'):''};
let s=fs.readFileSync('src.html','utf8');
for(const[k,v]of Object.entries(rep)) s=s.split(k).join(v);
fs.writeFileSync('sterne.html',s); console.log((s.length/1e6).toFixed(1)+' MB');
