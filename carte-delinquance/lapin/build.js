const fs=require('fs'), N='../node_modules/', b64=p=>fs.readFileSync(p).toString('base64');
const imgs={lapin_assis:'lapin_assis.png',lapin_court:'lapin_court.png',lapin_saute:'lapin_saute.png',lapins_groupe:'lapins_groupe.png'};
const rep={__M600__:b64(N+'@fontsource/montserrat/files/montserrat-latin-600-normal.woff2'),
 __M800__:b64(N+'@fontsource/montserrat/files/montserrat-latin-800-normal.woff2'),
 __M900__:b64(N+'@fontsource/montserrat/files/montserrat-latin-900-normal.woff2'),
 __D3__:fs.readFileSync(N+'d3/dist/d3.min.js','utf8'),
 __TOPOJSON__:fs.readFileSync(N+'topojson-client/dist/topojson-client.min.js','utf8'),
 __WORLD__:fs.readFileSync(N+'world-atlas/countries-50m.json','utf8'),
 __TL__:fs.readFileSync('timeline.json','utf8'),
 __IMGS__:JSON.stringify({...Object.fromEntries(Object.entries(imgs).map(([k,f])=>[k,'data:image/png;base64,'+b64(f)])),austin:'data:image/jpeg;base64,'+b64('austin_card.jpg')}), __LILITA__:b64(N+'@fontsource/lilita-one/files/lilita-one-latin-400-normal.woff2'),
 __TEXWORLD__:'data:image/jpeg;base64,'+b64('tex_world.jpg'), __TEXEU__:'data:image/jpeg;base64,'+b64('tex_region.jpg'),
 __AUDIO__:fs.existsSync('mix.m4a')?'data:audio/mp4;base64,'+b64('mix.m4a'):''};
let s=fs.readFileSync('src.html','utf8');
for(const[k,v]of Object.entries(rep)) s=s.split(k).join(v);
fs.writeFileSync('lapin.html',s); console.log((s.length/1e6).toFixed(1)+' MB');
