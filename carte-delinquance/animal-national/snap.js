// node snap.js plan | snap t1 t2 ... | frames a b
const {chromium}=require('../node_modules/playwright-core'); const fs=require('fs');
(async()=>{
 const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await br.newPage({viewport:{width:540,height:960}});
 p.on('pageerror',e=>console.error('ERR',e.message)); p.on('console',m=>{ if(m.type()==='error') console.error('CONSOLE',m.text()); });
 await p.goto('http://localhost:8765/animal/page.html'); await p.evaluate('window.ready');
 const [mode,...a]=process.argv.slice(2);
 if(mode==='plan'){ fs.writeFileSync('plan.json',JSON.stringify(await p.evaluate('window.plan()'))); }
 else if(mode==='snap'){ for(const t of a.map(Number)){ const d=await p.evaluate(async t=>{await window.prep(t);renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.9)},t);
   fs.writeFileSync(`snaps/s-${t.toFixed(2)}.jpg`,Buffer.from(d.split(',')[1],'base64')); } }
 else { const [f0,f1]=a.map(Number); fs.mkdirSync('frames',{recursive:true}); const t0=Date.now();
   
   for(let i=f0;i<f1;i++){ const fn=`frames/${String(i).padStart(5,'0')}.jpg`; if(fs.existsSync(fn)) continue;
     const d=await p.evaluate(async t=>{await window.prep(t);renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.93)},i/30);
     fs.writeFileSync(fn,Buffer.from(d.split(',')[1],'base64')); }
   console.log(`${f0}-${f1} ${((Date.now()-t0)/(f1-f0)|0)} ms/frame`); }
 await br.close();})();
