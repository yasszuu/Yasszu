// Usage: node render.mjs [--frames 0,90,200] [--scale 0.5] [--out paris-drone.mp4]
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const scale = +(args.scale || 1);
const W = Math.round(1080 * scale / 2) * 2, H = Math.round(1920 * scale / 2) * 2;
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
page.on('console', (m) => console.log('[page]', m.text()));
page.on('pageerror', (e) => console.error('[pageerror]', e));
await page.goto(`http://localhost:${port}/index.html?w=${W}&h=${H}`);
await page.waitForFunction(() => window.READY === true, null, { timeout: 300000 });
console.log('ready', await page.evaluate(() => window.STATS));
const total = await page.evaluate(() => window.FRAMES);

if (args.frames) {
  const dir = path.join(root, args.outdir || 'stills'); fs.mkdirSync(dir, { recursive: true });
  for (const f of args.frames.split(',').map(Number)) {
    const t0 = Date.now();
    const url = await page.evaluate((i) => window.renderFrame(i, 'image/jpeg'), f);
    fs.writeFileSync(path.join(dir, `f${String(f).padStart(3, '0')}.jpg`), Buffer.from(url.split(',')[1], 'base64'));
    console.log(`frame ${f} ${Date.now() - t0}ms`);
  }
} else {
  const out = path.join(root, args.out || 'paris-drone.mp4');
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', '30', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const start = Date.now();
  for (let i = 0; i < total; i++) {
    const url = await page.evaluate((f) => window.renderFrame(f), i);
    const buf = Buffer.from(url.split(',')[1], 'base64');
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 10 === 0) console.log(`frame ${i}/${total}  ${((Date.now() - start) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close();
server.close();
