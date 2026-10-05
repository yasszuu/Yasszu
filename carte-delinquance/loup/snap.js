const {chromium}=require('../node_modules/playwright-core'); const fs=require('fs');
(async()=>{
 const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await br.newPage({viewport:{width:540,height:960}});
 p.on('pageerror',e=>console.error('ERR',e.message)); p.on('console',m=>console.log('LOG',m.text()));
 await p.goto('file://'+__dirname+'/loup.html?capture'); await p.evaluate('window.ready');
 for(const t of process.argv.slice(2).map(Number)){
   const d=await p.evaluate(t=>{renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.85)},t);
   fs.writeFileSync(`snap-${t.toFixed(2)}.jpg`,Buffer.from(d.split(',')[1],'base64')); }
 await br.close();})();
