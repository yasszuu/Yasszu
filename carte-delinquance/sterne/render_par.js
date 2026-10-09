// Rendu d'une tranche d'images en JPEG : node render_par.js <début> <fin>
const {chromium}=require('../../node_modules/playwright-core'); const fs=require('fs');
const FPS=30, [a,b]=process.argv.slice(2).map(Number);
(async()=>{
 const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--allow-file-access-from-files']});
 const p=await br.newPage({viewport:{width:540,height:960}});
 await p.goto('file://'+__dirname+'/sterne.html?capture'); await p.evaluate('window.ready');
 fs.mkdirSync('frames',{recursive:true}); const t0=Date.now();
 for(let i=a;i<b;i++){
   if(fs.existsSync(`frames/${String(i).padStart(5,'0')}.jpg`)) continue;
   const d=await p.evaluate(async t=>{await window.prep(t);renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.93)},i/FPS);
   fs.writeFileSync(`frames/${String(i).padStart(5,'0')}.jpg`,Buffer.from(d.split(',')[1],'base64'));
 }
 console.log(`${a}-${b} ${((Date.now()-t0)/(b-a)|0)} ms/frame`); await br.close();
})();
