const {chromium}=require('../node_modules/playwright-core'); const fs=require('fs');
(async()=>{
 const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await br.newPage({viewport:{width:540,height:960}});
 p.on('pageerror',e=>console.error('ERR',e.message)); p.on('console',m=>console.log('LOG',m.text()));
 await p.goto('http://localhost:8765/sterne/demo.html'); await p.waitForFunction('window.ready===true',null,{timeout:180000});
 const [mode,...ts]=process.argv.slice(2); 
 if(mode==='snap'){ for(const t of ts.map(Number)){ const d=await p.evaluate(t=>{renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.9)},t);
   fs.writeFileSync(`s-${t.toFixed(2)}.jpg`,Buffer.from(d.split(',')[1],'base64')); } }
 else { const [a,b]=ts.map(Number); fs.mkdirSync('frames',{recursive:true}); const t0=Date.now();
   for(let i=a;i<b;i++){ const d=await p.evaluate(t=>{renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.93)},i/30);
     fs.writeFileSync(`frames/${String(i).padStart(4,'0')}.jpg`,Buffer.from(d.split(',')[1],'base64')); }
   console.log(a,b,((Date.now()-t0)/(b-a)|0),'ms/frame'); }
 await br.close();})();
