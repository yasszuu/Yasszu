const {chromium}=require('../node_modules/playwright-core'); const {spawn}=require('child_process'); const fs=require('fs');
const FPS=+process.env.FPS||30, frames=process.argv.slice(2).map(Number);
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:540,height:960}});
 p.on('pageerror',e=>console.error('ERR',e.message)); p.on('console',m=>m.type()==='error'&&console.error('CONSOLE',m.text()));
 await p.goto('file://'+__dirname+'/departements-criminogenes.html?capture'); await p.evaluate('window.ready');
 const grab=async t=>Buffer.from((await p.evaluate(t=>{renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.93)},t)).split(',')[1],'base64');
 if(frames.length){ for(const t of frames) fs.writeFileSync(`snap-${t}.jpg`,await grab(t)); await b.close(); return; }
 const D=await p.evaluate('DURATION'), n=Math.ceil(D*FPS);
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-i','mix.wav',
   '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','departements-criminogenes.mp4'],{stdio:['pipe','ignore','inherit']});
 const t0=Date.now();
 for(let i=0;i<n;i++){ ff.stdin.write(await grab(i/FPS)); if(i%150==0)console.log(i+'/'+n, ((Date.now()-t0)/1000|0)+'s'); }
 ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close();
})();
