// node gsnap.js plan | snap t1 t2 ... | frames a b
const {chromium}=require('../node_modules/playwright-core'); const fs=require('fs');
(async()=>{
 const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await br.newPage({viewport:{width:540,height:960}});
 p.on('pageerror',e=>console.error('ERR',e.message));
 await p.goto('http://localhost:8765/gombe/map_built.html'); await p.evaluate('window.ready');
 const [mode,...a]=process.argv.slice(2);
 if(mode==='plan'){ fs.writeFileSync('plan.json',JSON.stringify(await p.evaluate('window.plan()'))); }
 else if(mode==='snap'){ for(const t of a.map(Number)){ const d=await p.evaluate(async t=>{await window.prep(t);renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.9)},t);
   fs.writeFileSync(`s-${t.toFixed(2)}.jpg`,Buffer.from(d.split(',')[1],'base64')); } }
 else { const [f0,f1]=a.map(Number); fs.mkdirSync('frames',{recursive:true});
   for(let i=f0;i<f1;i++){ const d=await p.evaluate(async t=>{await window.prep(t);renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.93)},i/30);
     fs.writeFileSync(`frames/${String(i).padStart(4,'0')}.jpg`,Buffer.from(d.split(',')[1],'base64')); } }
 await br.close();})();
