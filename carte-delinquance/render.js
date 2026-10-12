const {chromium}=require('playwright-core'); const {spawn}=require('child_process');
const FPS=+process.env.FPS||30, frames=process.argv.slice(2).map(Number);
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
 const p=await b.newPage({viewport:{width:540,height:960}});
 p.on('pageerror',e=>console.error('ERR',e.message));
 await p.goto('file://'+__dirname+'/carte-delinquance.html?capture'); await p.evaluate('window.ready');
 const grab=async t=>Buffer.from((await p.evaluate(t=>{renderAt(t);return document.getElementById('c').toDataURL('image/jpeg',0.95)},t)).split(',')[1],'base64');
 if(frames.length){ for(const t of frames) require('fs').writeFileSync(`snap-${t}.jpg`,await grab(t)); await b.close(); return; }
 const D=await p.evaluate('DURATION'), n=Math.round(D*FPS);
 const ff=spawn('ffmpeg',['-y','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-movflags','+faststart','carte-delinquance.mp4'],{stdio:['pipe','ignore','inherit']});
 for(let i=0;i<n;i++){ ff.stdin.write(await grab(i/FPS)); if(i%60==0)console.log(i+'/'+n); }
 ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close();
})();
