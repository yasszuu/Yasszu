const { chromium } = require('playwright');
const { spawn } = require('child_process');
(async () => {
  const mode = process.argv[2] || 'test';
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => m.type() === 'error' && console.log('CERR', m.text()));
  await p.goto('http://localhost:8766/index.html');
  await p.waitForFunction(() => window.ready, null, { timeout: 120000 });
  if (mode === 'test') {
    const times = (process.argv[3] || '1.8,5.0,5.9,8.5,9.8,13,16.0,16.6,18.2,19.2').split(',').map(Number);
    for (const t of times) {
      const s = Date.now();
      await p.evaluate(t => window.renderAt(t), t);
      await p.screenshot({ path: `f_${t}.jpg`, type: 'jpeg', quality: 80 });
      console.log(t, Date.now() - s, 'ms');
    }
  } else {
    const ff = spawn(process.env.FF, ['-y', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', 'video.mp4'], { stdio: ['pipe', 'ignore', 'inherit'] });
    for (let f = 0; f < 600; f++) {
      await p.evaluate(t => window.renderAt(t), f / 30);
      const buf = await p.screenshot({ type: 'jpeg', quality: 94 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 30 === 0) console.log('frame', f);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await b.close();
})();
