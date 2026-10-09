// Paris drone shot — procedural 3D motion design scene.
// Rendered deterministically frame by frame: window.renderFrame(i) -> PNG data URL.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const params = new URLSearchParams(location.search);
const W = +(params.get('w') || 1080);
const H = +(params.get('h') || 1920);
const FPS = 30;
const DURATION = 12;
window.FRAMES = FPS * DURATION;

// ---------------------------------------------------------------- utils
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(1337);
const R = (a, b) => a + (b - a) * rand();
const pick = (arr) => arr[Math.floor(rand() * arr.length)];
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;
const col = (hex) => new THREE.Color(hex);
const jitter = (c, amt) => { const k = 1 + (rand() - 0.5) * amt; return new THREE.Color(c.r * k, c.g * k, c.b * k); };

// ---------------------------------------------------------------- renderer
const canvas = document.createElement('canvas');
canvas.width = W; canvas.height = H;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const outCanvas = document.createElement('canvas');
outCanvas.width = W; outCanvas.height = H;
document.body.appendChild(outCanvas);
const out2d = outCanvas.getContext('2d');

const scene = new THREE.Scene();
const FOG = col('#f2c9a0');
scene.fog = new THREE.FogExp2(FOG, 0.00085);
scene.background = FOG;

const camera = new THREE.PerspectiveCamera(70, W / H, 0.2, 4000);

// ---------------------------------------------------------------- textures
function canvasTex(w, h, draw, { srgb = true } = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}
function speckle(g, w, h, n, colors, size = 2) {
  for (let i = 0; i < n; i++) { g.fillStyle = pick(colors); g.fillRect(rand() * w, rand() * h, size * rand() + 0.5, size * rand() + 0.5); }
}

const texUpper = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = '#f1e9da'; g.fillRect(0, 0, w, h);
  speckle(g, w, h, 2200, ['rgba(120,100,70,0.07)', 'rgba(255,255,255,0.1)']);
  g.strokeStyle = 'rgba(120,100,80,0.16)'; g.lineWidth = 1.5;
  for (let y = 0; y < h; y += 32) { g.beginPath(); g.moveTo(0, y + 0.5); g.lineTo(w, y + 0.5); g.stroke(); }
  const wx = 80, wy = 46, ww = 96, wh = 176;
  g.fillStyle = '#e4d8c2'; g.fillRect(wx - 10, wy - 12, ww + 20, wh + 12);
  g.fillStyle = '#d4c5aa'; g.fillRect(wx - 16, wy - 24, ww + 32, 12);
  g.fillStyle = 'rgba(0,0,0,0.14)'; g.fillRect(wx - 16, wy - 12, ww + 32, 3);
  g.fillStyle = '#f7f3ec'; g.fillRect(wx, wy, ww, wh);
  const gr = g.createLinearGradient(wx, wy, wx + ww, wy + wh);
  gr.addColorStop(0, '#6a7f93'); gr.addColorStop(0.42, '#2b3947'); gr.addColorStop(0.55, '#3e5266'); gr.addColorStop(1, '#1b2531');
  g.fillStyle = gr; g.fillRect(wx + 7, wy + 7, ww - 14, wh - 14);
  g.fillStyle = 'rgba(255,225,190,0.2)';
  g.beginPath(); g.moveTo(wx + 7, wy + 64); g.lineTo(wx + 44, wy + 7); g.lineTo(wx + 62, wy + 7); g.lineTo(wx + 7, wy + 98); g.fill();
  g.fillStyle = 'rgba(240,228,210,0.3)'; g.fillRect(wx + 9, wy + 9, 13, wh - 18); g.fillRect(wx + ww - 22, wy + 9, 13, wh - 18);
  g.fillStyle = '#f7f3ec'; g.fillRect(wx + ww / 2 - 3, wy, 6, wh);
  for (const fy of [0.33, 0.62]) g.fillRect(wx, wy + wh * fy, ww, 4);
  g.fillStyle = '#1b1d20'; g.fillRect(wx - 4, wy + wh - 50, ww + 8, 4); g.fillRect(wx - 4, wy + wh - 6, ww + 8, 4);
  for (let x = wx; x <= wx + ww; x += 8) g.fillRect(x, wy + wh - 50, 2, 48);
  g.strokeStyle = '#1b1d20'; g.lineWidth = 2;
  for (let x = wx + 4; x < wx + ww; x += 16) { g.beginPath(); g.arc(x + 4, wy + wh - 28, 6, 0, Math.PI * 2); g.stroke(); }
  g.fillStyle = '#d9ccb4'; g.fillRect(wx - 12, wy + wh, ww + 24, 8);
  g.fillStyle = 'rgba(0,0,0,0.16)'; g.fillRect(wx - 12, wy + wh + 8, ww + 24, 3);
});

const texGround = canvasTex(256, 360, (g, w, h) => {
  g.fillStyle = '#e8dfcc'; g.fillRect(0, 0, w, h);
  speckle(g, w, h, 2000, ['rgba(110,90,60,0.08)', 'rgba(255,255,255,0.1)']);
  g.fillStyle = 'rgba(90,75,55,0.28)';
  for (let y = 0; y < h; y += 36) g.fillRect(0, y, w, 4);
  // shop front
  const x0 = 30, x1 = 226, y0 = 64;
  g.fillStyle = '#22302a'; g.fillRect(x0, y0, x1 - x0, h - y0);
  g.fillStyle = '#c9a85a'; g.fillRect(x0 + 10, y0 + 10, x1 - x0 - 20, 4);
  g.fillStyle = '#1a231f'; g.fillRect(x0 + 8, y0 + 18, x1 - x0 - 16, 34);
  g.fillStyle = 'rgba(232,200,120,0.85)';
  for (let x = x0 + 26; x < x1 - 26; x += 14) g.fillRect(x, y0 + 30, 8, 10);
  const gl = g.createLinearGradient(0, y0 + 60, 0, h);
  gl.addColorStop(0, '#3b2f25'); gl.addColorStop(0.6, '#a46c3c'); gl.addColorStop(1, '#e9b779');
  g.fillStyle = gl; g.fillRect(x0 + 10, y0 + 62, x1 - x0 - 20, h - y0 - 62);
  g.fillStyle = 'rgba(40,25,15,0.55)';
  for (let y = y0 + 120; y < h - 20; y += 52) g.fillRect(x0 + 14, y, x1 - x0 - 28, 5);
  g.fillStyle = 'rgba(255,240,215,0.22)';
  g.beginPath(); g.moveTo(x0 + 10, y0 + 140); g.lineTo(x0 + 90, y0 + 62); g.lineTo(x0 + 120, y0 + 62); g.lineTo(x0 + 10, y0 + 190); g.fill();
  g.fillStyle = '#22302a'; g.fillRect(w / 2 - 3, y0 + 60, 6, h - y0 - 60);
  // keystone
  g.fillStyle = '#d7c9ad'; g.fillRect(w / 2 - 16, y0 - 26, 32, 34);
});

const texRoof = canvasTex(128, 128, (g, w, h) => {
  g.fillStyle = '#8b97a3'; g.fillRect(0, 0, w, h);
  speckle(g, w, h, 600, ['rgba(255,255,255,0.08)', 'rgba(0,0,0,0.08)']);
  for (let x = 0; x < w; x += 32) {
    g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(x, 0, 3, h);
    g.fillStyle = 'rgba(0,0,0,0.22)'; g.fillRect(x + 3, 0, 3, h);
  }
  for (let i = 0; i < 6; i++) { g.fillStyle = 'rgba(40,50,60,0.07)'; g.fillRect(rand() * w, 0, 10 + rand() * 20, h); }
});

const texAsphalt = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = '#4a4c51'; g.fillRect(0, 0, w, h);
  speckle(g, w, h, 9000, ['rgba(255,255,255,0.07)', 'rgba(0,0,0,0.12)', 'rgba(120,110,100,0.1)'], 2);
  for (let i = 0; i < 5; i++) { g.strokeStyle = 'rgba(25,25,28,0.35)'; g.lineWidth = 1.5; g.beginPath(); let x = rand() * w, y = rand() * h; g.moveTo(x, y); for (let k = 0; k < 6; k++) { x += R(-20, 20); y += R(-20, 20); g.lineTo(x, y); } g.stroke(); }
});

const texSidewalk = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = '#b9b3a8'; g.fillRect(0, 0, w, h);
  for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
    const v = 175 + Math.floor(R(-12, 12)); g.fillStyle = `rgb(${v + 8},${v + 3},${v - 6})`; g.fillRect(x * 64 + 2, y * 64 + 2, 60, 60);
  }
  speckle(g, w, h, 2500, ['rgba(0,0,0,0.08)', 'rgba(255,255,255,0.1)']);
});

const texPaving = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#8f877b'; g.fillRect(0, 0, w, h);
  const n = 16, s = w / n;
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const off = (y % 2) * s * 0.5;
    const v = 186 + Math.floor(R(-18, 14));
    g.fillStyle = `rgb(${v + 6},${v},${v - 10})`;
    g.fillRect(x * s + off + 1.5, y * s + 1.5, s - 3, s - 3);
    if (off) g.fillRect(-s + off + 1.5 + x * 0, y * s + 1.5, s - 3, s - 3);
  }
  speckle(g, w, h, 5000, ['rgba(0,0,0,0.07)', 'rgba(255,255,255,0.09)']);
});

const texLawn = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = '#6f8f45'; g.fillRect(0, 0, w, h);
  for (let x = 0; x < w; x += 32) { g.fillStyle = (x / 32) % 2 ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.04)'; g.fillRect(x, 0, 32, h); }
  speckle(g, w, h, 4000, ['rgba(40,70,20,0.2)', 'rgba(170,200,110,0.15)']);
});

const texLattice = canvasTex(128, 128, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  g.strokeStyle = '#fff'; g.lineWidth = 5;
  g.strokeRect(2, 2, w - 4, h - 4);
  g.lineWidth = 3;
  g.beginPath(); g.moveTo(0, 0); g.lineTo(w, h); g.moveTo(w, 0); g.lineTo(0, h); g.stroke();
  g.lineWidth = 1.5;
  g.beginPath(); g.moveTo(w / 2, 0); g.lineTo(w / 2, h); g.moveTo(0, h / 2); g.lineTo(w, h / 2); g.stroke();
}, { srgb: false });

const texPoster = canvasTex(512, 128, (g, w, h) => {
  const cols = ['#d6402f', '#f2c14e', '#2f5d8a', '#efe6d2', '#1b1b1b', '#7aa36b', '#e98a4a'];
  let x = 0;
  while (x < w) { const pw = R(40, 90); g.fillStyle = pick(cols); g.fillRect(x, 0, pw, h); g.fillStyle = 'rgba(255,255,255,0.8)'; g.fillRect(x + 8, 14, pw - 16, 8); g.fillRect(x + 8, 28, (pw - 16) * 0.6, 5); g.fillStyle = 'rgba(0,0,0,0.5)'; g.fillRect(x + 8, h - 30, pw - 16, 14); x += pw + 3; }
});

// ---------------------------------------------------------------- materials
const matUpper = new THREE.MeshStandardMaterial({ map: texUpper, vertexColors: true, roughness: 0.88 });
const matGround = new THREE.MeshStandardMaterial({ map: texGround, vertexColors: true, roughness: 0.85 });
const matPlain = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9 });
const matRoof = new THREE.MeshStandardMaterial({ map: texRoof, vertexColors: true, roughness: 0.55, metalness: 0.25 });
const matSidewalk = new THREE.MeshStandardMaterial({ map: texSidewalk, vertexColors: true, roughness: 0.95 });

// ---------------------------------------------------------------- geometry builder
class GB {
  constructor() { this.p = []; this.n = []; this.uv = []; this.c = []; }
  quad(a, b, c, d, ua, ub, uc, ud, color) {
    const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
    const l = Math.hypot(nx, ny, nz) || 1; nx /= l; ny /= l; nz /= l;
    for (const [p, u] of [[a, ua], [b, ub], [c, uc], [a, ua], [c, uc], [d, ud]]) {
      this.p.push(p[0], p[1], p[2]); this.n.push(nx, ny, nz); this.uv.push(u[0], u[1]); this.c.push(color.r, color.g, color.b);
    }
  }
  // axis aligned box; s>0 => world-space UVs with scale s
  box(x0, y0, z0, x1, y1, z1, color, s = 0, top = true, bottom = false) {
    const U = (u, v) => (s ? [u / s, v / s] : [u, v]);
    const dx = s ? 1 : 0;
    const f = (a, b, c, d, ua, ub, uc, ud) => this.quad(a, b, c, d, ua, ub, uc, ud, color);
    // +x
    f([x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], U(-z1, y0), U(-z0, y0), U(-z0, y1), U(-z1, y1));
    f([x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0], U(z0, y0), U(z1, y0), U(z1, y1), U(z0, y1));
    f([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], U(x0, y0), U(x1, y0), U(x1, y1), U(x0, y1));
    f([x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], U(-x1, y0), U(-x0, y0), U(-x0, y1), U(-x1, y1));
    if (top) f([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], U(x0, -z1), U(x1, -z1), U(x1, -z0), U(x0, -z0));
    if (bottom) f([x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1], U(x0, z0), U(x1, z0), U(x1, z1), U(x0, z1));
    void dx;
  }
  get empty() { return this.p.length === 0; }
  build() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3));
    g.computeBoundingSphere(); g.computeBoundingBox();
    return g;
  }
}

// frame for a facade: C = face center (x,z), N outward normal, Rv right vector
function frame(cx, cz, nx, nz) {
  const rx = nz, rz = -nx;
  return {
    // local (along, y, out) -> world
    P: (a, y, o) => [cx + rx * a + nx * o, y, cz + rz * a + nz * o],
    box(gb, a0, a1, y0, y1, o0, o1, color) {
      const p1 = this.P(a0, y0, o0), p2 = this.P(a1, y1, o1);
      gb.box(Math.min(p1[0], p2[0]), y0, Math.min(p1[2], p2[2]), Math.max(p1[0], p2[0]), y1, Math.max(p1[2], p2[2]), color);
    },
  };
}

// ---------------------------------------------------------------- city layout
const STONES = ['#f4e8d2', '#efe2c8', '#e8dbc0', '#f6eddc', '#e4d4b8', '#ecdcc0', '#f0e4d0', '#e9e0d2'].map(col);
const ZINCS = ['#8f9ba7', '#808c98', '#97a3ad', '#7a8793', '#8a949c'].map(col);
const AWNINGS = ['#9e2328', '#1f4d3a', '#1d2c4d', '#6d1f2c', '#2a2a2a', '#b5552a'].map(col);
const IRON = col('#202326');
const GLASS = col('#2b3744');
const BRICK = ['#b8653e', '#a95a37', '#c27a52'].map(col);

const xLines = [{ c: 0, w: 30 }];
for (let k = 1; k <= 5; k++) { xLines.push({ c: 115 * k, w: 14 }); xLines.push({ c: -115 * k, w: 14 }); }
xLines.sort((a, b) => a.c - b.c);
const zLines = [];
for (let k = 0; k <= 9; k++) zLines.push({ c: 50 + 100 * k, w: 14 });
for (let k = 0; k <= 10; k++) zLines.push({ c: -50 - 100 * k, w: 14 });
zLines.sort((a, b) => a.c - b.c);

const PLAZA = { x0: -52, x1: 52, z0: -43, z1: 43 };
const TOWER = { x: -172.5, z: -700 };
const MAN = new THREE.Vector3(7, 0.15, 6);
const FOUNTAIN = new THREE.Vector3(0, 0.15, -9);

const cityGroup = new THREE.Group(); scene.add(cityGroup);
const sidewalkGB = new GB();

function addBuilding(b, gbs, detailed) {
  const { x0, x1, z0, z1, nx, nz, Hc, nUp } = b;
  const alongZ = nx !== 0;
  const L = alongZ ? z1 - z0 : x1 - x0;
  const D = alongZ ? x1 - x0 : z1 - z0;
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  const stone = b.stone, zinc = b.zinc;
  const nb = Math.max(1, Math.round(L / 3.3));
  const ff = frame(cx + nx * D / 2, cz + nz * D / 2, nx, nz);
  const fb = frame(cx - nx * D / 2, cz - nz * D / 2, -nx, -nz);
  const rx = nz, rz = -nx;
  const fs1 = frame(cx + rx * L / 2, cz + rz * L / 2, rx, rz);
  const fs2 = frame(cx - rx * L / 2, cz - rz * L / 2, -rx, -rz);
  const GH = 4.5;
  for (const f of [ff, fb]) {
    gbs.ground.quad(f.P(-L / 2, 0, 0), f.P(L / 2, 0, 0), f.P(L / 2, GH, 0), f.P(-L / 2, GH, 0), [0, 0], [nb, 0], [nb, 1], [0, 1], stone);
    gbs.upper.quad(f.P(-L / 2, GH, 0), f.P(L / 2, GH, 0), f.P(L / 2, Hc, 0), f.P(-L / 2, Hc, 0), [0, 0], [nb, 0], [nb, nUp], [0, nUp], stone);
  }
  const side = jitter(stone, 0.06).multiplyScalar(0.94);
  for (const f of [fs1, fs2]) gbs.plain.quad(f.P(-D / 2, 0, 0), f.P(D / 2, 0, 0), f.P(D / 2, Hc, 0), f.P(-D / 2, Hc, 0), [0, 0], [1, 0], [1, 1], [0, 1], side);

  // mansard roof
  const rh = b.roofH, ins = 1.6;
  for (const f of [ff, fb]) gbs.roof.quad(f.P(-L / 2, Hc, 0), f.P(L / 2, Hc, 0), f.P(L / 2, Hc + rh, -ins), f.P(-L / 2, Hc + rh, -ins), [0, 0], [L / 1.2, 0], [L / 1.2, 3], [0, 3], zinc);
  for (const f of [fs1, fs2]) gbs.plain.quad(f.P(-D / 2, Hc, 0), f.P(D / 2, Hc, 0), f.P(D / 2 - ins, Hc + rh, 0), f.P(-D / 2 + ins, Hc + rh, 0), [0, 0], [1, 0], [1, 1], [0, 1], side);
  const zTop = zinc.clone().multiplyScalar(0.8);
  gbs.roof.quad(ff.P(-L / 2, Hc + rh, -ins), ff.P(L / 2, Hc + rh, -ins), ff.P(L / 2, Hc + rh, -(D - ins)), ff.P(-L / 2, Hc + rh, -(D - ins)), [0, 0], [L / 1.2, 0], [L / 1.2, D / 1.2], [0, D / 1.2], zTop);

  // cornice + string course
  const corn = jitter(stone, 0.04).multiplyScalar(1.02);
  ff.box(gbs.plain, -L / 2, L / 2, Hc - 0.32, Hc + 0.12, 0, 0.45, corn);
  ff.box(gbs.plain, -L / 2, L / 2, GH - 0.1, GH + 0.18, 0, 0.14, corn);

  // chimneys
  const nCh = 1 + Math.floor(rand() * (detailed ? 3 : 2));
  for (let i = 0; i < nCh; i++) {
    const a = R(-L / 2 + 1, L / 2 - 1), o = -R(ins + 0.5, D - ins - 2.5);
    const bc = rand() < 0.6 ? pick(BRICK) : jitter(stone, 0.05);
    const h = R(1.2, 2.2);
    ff.box(gbs.plain, a - 0.35, a + 0.35, Hc + rh - 0.2, Hc + rh + h, o - 2.0, o, bc);
    if (detailed) {
      const pots = 2 + Math.floor(rand() * 4);
      for (let k = 0; k < pots; k++) {
        const po = o - 0.25 - k * (1.5 / Math.max(1, pots - 1));
        ff.box(gbs.plain, a - 0.1, a + 0.1, Hc + rh + h, Hc + rh + h + 0.45, po - 0.1, po + 0.1, col('#c06a3c'));
      }
    }
  }

  if (!detailed) return;
  // balconies (2nd & top floor)
  for (const yb of [GH + 3.2, GH + (nUp - 1) * 3.2]) {
    ff.box(gbs.plain, -L / 2 + 0.15, L / 2 - 0.15, yb - 0.16, yb, 0, 0.6, corn);
    ff.box(gbs.plain, -L / 2 + 0.15, L / 2 - 0.15, yb, yb + 0.9, 0.56, 0.6, IRON);
    ff.box(gbs.plain, -L / 2 + 0.15, L / 2 - 0.15, yb + 0.86, yb + 0.92, 0.5, 0.62, IRON);
  }
  // dormers
  const bw = L / nb;
  const dorm = jitter(stone, 0.04).multiplyScalar(1.03);
  for (let i = 0; i < nb; i++) {
    const a = -L / 2 + (i + 0.5) * bw;
    ff.box(gbs.plain, a - 0.55, a + 0.55, Hc + 0.3, Hc + 1.95, -1.7, -0.25, dorm);
    gbs.plain.quad(ff.P(a - 0.32, Hc + 0.5, -0.24), ff.P(a + 0.32, Hc + 0.5, -0.24), ff.P(a + 0.32, Hc + 1.65, -0.24), ff.P(a - 0.32, Hc + 1.65, -0.24), [0, 0], [1, 0], [1, 1], [0, 1], GLASS);
    // little gable cap
    gbs.roof.quad(ff.P(a - 0.68, Hc + 1.95, -0.15), ff.P(a + 0.68, Hc + 1.95, -0.15), ff.P(a + 0.68, Hc + 2.35, -0.95), ff.P(a - 0.68, Hc + 2.35, -0.95), [0, 0], [1, 0], [1, 1], [0, 1], zinc);
  }
  // awnings on shops
  if (b.awning) {
    const ac = b.awning;
    for (let i = 0; i < nb; i++) {
      if (rand() < 0.25) continue;
      const a = -L / 2 + (i + 0.5) * bw, hw = bw * 0.44;
      gbs.plain.quad(ff.P(a - hw, 3.85, 0.05), ff.P(a + hw, 3.85, 0.05), ff.P(a + hw, 3.2, 1.5), ff.P(a - hw, 3.2, 1.5), [0, 0], [1, 0], [1, 1], [0, 1], ac);
      gbs.plain.quad(ff.P(a - hw, 2.9, 1.5), ff.P(a + hw, 2.9, 1.5), ff.P(a + hw, 3.2, 1.5), ff.P(a - hw, 3.2, 1.5), [0, 0], [1, 0], [1, 1], [0, 1], ac.clone().multiplyScalar(0.8));
    }
  }
}

function addSidewalk(x0, x1, z0, z1, y = 0.15) {
  sidewalkGB.box(x0, 0, z0, x1, y, z1, jitter(col('#ffffff'), 0.05), 4);
}

let buildingCount = 0;
for (let i = 0; i < xLines.length - 1; i++) {
  for (let j = 0; j < zLines.length - 1; j++) {
    const xa = xLines[i], xb = xLines[i + 1], za = zLines[j], zb = zLines[j + 1];
    let bx0 = xa.c + xa.w / 2, bx1 = xb.c - xb.w / 2, bz0 = za.c + za.w / 2, bz1 = zb.c - zb.w / 2;
    const cxm = (bx0 + bx1) / 2, czm = (bz0 + bz1) / 2;
    // park around the tower
    if (Math.abs(cxm - TOWER.x) < 10 && czm > -960 && czm < -440) continue;
    const sw = { x0: xa.w === 30 ? 4.5 : 3, x1: xb.w === 30 ? 4.5 : 3, z0: 3, z1: 3 };
    // trim blocks next to the plaza
    const touchesPlaza = bz0 < PLAZA.z1 && bz1 > PLAZA.z0 && bx0 < PLAZA.x1 && bx1 > PLAZA.x0;
    if (touchesPlaza) {
      if (cxm > 0) { bx0 = PLAZA.x1; sw.x0 = 0; } else { bx1 = PLAZA.x0; sw.x1 = 0; }
    }
    addSidewalk(bx0 - sw.x0, bx1 + sw.x1, bz0 - sw.z0, bz1 + sw.z1);

    const detailed = Math.abs(cxm) < 240 && czm > -500;
    const gbs = { ground: new GB(), upper: new GB(), plain: new GB(), roof: new GB() };
    const D = 12.5;
    const sides = [
      { nx: 0, nz: 1, a0: bx0, a1: bx1, fixed: bz1, full: true },
      { nx: 0, nz: -1, a0: bx0, a1: bx1, fixed: bz0, full: true },
      { nx: 1, nz: 0, a0: bz0 + D, a1: bz1 - D, fixed: bx1, full: false },
      { nx: -1, nz: 0, a0: bz0 + D, a1: bz1 - D, fixed: bx0, full: false },
    ];
    for (const s of sides) {
      let a = s.a0;
      while (a < s.a1 - 0.5) {
        let w = R(10, 17);
        if (s.a1 - (a + w) < 8) w = s.a1 - a;
        const a2 = a + w;
        const nUp = rand() < 0.75 ? 5 : 4;
        const Hc = 4.5 + nUp * 3.2;
        let bb;
        if (s.nz !== 0) {
          const zf = s.fixed, zbk = s.nz > 0 ? zf - D : zf + D;
          bb = { x0: a, x1: a2, z0: Math.min(zf, zbk), z1: Math.max(zf, zbk) };
        } else {
          const xf = s.fixed, xbk = s.nx > 0 ? xf - D : xf + D;
          bb = { x0: Math.min(xf, xbk), x1: Math.max(xf, xbk), z0: a, z1: a2 };
        }
        Object.assign(bb, { nx: s.nx, nz: s.nz, Hc, nUp, roofH: R(3.0, 3.8), stone: jitter(pick(STONES), 0.05), zinc: jitter(pick(ZINCS), 0.08), awning: rand() < 0.55 ? pick(AWNINGS) : null });
        addBuilding(bb, gbs, detailed);
        buildingCount++;
        a = a2;
      }
    }
    for (const [k, m] of [['ground', matGround], ['upper', matUpper], ['plain', matPlain], ['roof', matRoof]]) {
      if (gbs[k].empty) continue;
      const mesh = new THREE.Mesh(gbs[k].build(), m);
      mesh.castShadow = true; mesh.receiveShadow = true;
      cityGroup.add(mesh);
    }
  }
}

// ground (asphalt)
{
  texAsphalt.repeat.set(400, 400);
  const g = new THREE.Mesh(new THREE.PlaneGeometry(3200, 3200), new THREE.MeshStandardMaterial({ map: texAsphalt, roughness: 0.95 }));
  g.rotation.x = -Math.PI / 2; g.receiveShadow = true; scene.add(g);
}
// plaza
{
  const gb = new GB();
  gb.box(PLAZA.x0, 0, PLAZA.z0, PLAZA.x1, 0.15, PLAZA.z1, col('#ffffff'), 0);
  const geo = gb.build();
  // world UVs on top
  const pos = geo.attributes.position, uv = geo.attributes.uv;
  for (let i = 0; i < pos.count; i++) uv.setXY(i, pos.getX(i) / 8, -pos.getZ(i) / 8);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: texPaving, roughness: 0.9 }));
  m.receiveShadow = true; scene.add(m);
  // decorative rings around fountain
  const ringMat = new THREE.MeshStandardMaterial({ color: '#7b7268', roughness: 0.9 });
  for (const [r0, r1] of [[7.2, 7.8], [11.5, 11.9], [16, 16.3]]) {
    const ring = new THREE.Mesh(new THREE.RingGeometry(r0, r1, 96), ringMat);
    ring.rotation.x = -Math.PI / 2; ring.position.set(FOUNTAIN.x, 0.152, FOUNTAIN.z); ring.receiveShadow = true; scene.add(ring);
  }
  // radial lines
  const lineMat = new THREE.MeshStandardMaterial({ color: '#a79e90', roughness: 0.9 });
  for (let k = 0; k < 16; k++) {
    const a = (k / 16) * Math.PI * 2;
    const l = new THREE.Mesh(new THREE.PlaneGeometry(0.18, 8.2), lineMat);
    l.rotation.x = -Math.PI / 2; l.rotation.z = a;
    l.position.set(FOUNTAIN.x + Math.sin(a) * 11.9, 0.151, FOUNTAIN.z + Math.cos(a) * 11.9);
    l.receiveShadow = true; scene.add(l);
  }
}
// park (Champ de Mars-ish)
{
  texLawn.repeat.set(10, 50);
  const lawn = new THREE.Mesh(new THREE.PlaneGeometry(90, 480), new THREE.MeshStandardMaterial({ map: texLawn, roughness: 1 }));
  lawn.rotation.x = -Math.PI / 2; lawn.position.set(TOWER.x, 0.06, -700); lawn.receiveShadow = true; scene.add(lawn);
}
{
  const sw = new THREE.Mesh(sidewalkGB.build(), matSidewalk);
  sw.receiveShadow = true; scene.add(sw);
}

// road markings
{
  const gb = new GB(); const white = col('#ecebe6');
  const isCross = (z) => zLines.some((l) => Math.abs(z - l.c) < 8);
  for (const zr of [[57, 990], [-1000, -57]]) {
    for (let z = zr[0]; z < zr[1]; z += 9) {
      if (isCross(z) || isCross(z + 3)) continue;
      for (const x of [-7, -3.5, 3.5, 7]) gb.quad([x - 0.08, 0.02, z + 3], [x + 0.08, 0.02, z + 3], [x + 0.08, 0.02, z], [x - 0.08, 0.02, z], [0, 0], [1, 0], [1, 1], [0, 1], white);
    }
    for (const x of [-0.25, 0.25]) gb.quad([x - 0.07, 0.02, zr[1]], [x + 0.07, 0.02, zr[1]], [x + 0.07, 0.02, zr[0]], [x - 0.07, 0.02, zr[0]], [0, 0], [1, 0], [1, 1], [0, 1], col('#e9e2c8'));
  }
  // zebra crossings
  for (const l of zLines) {
    for (const zc of [l.c - l.w / 2 - 2.5, l.c + l.w / 2 + 2.5]) {
      if (Math.abs(zc) < 45) continue;
      for (let x = -10; x < 10; x += 1.1) gb.quad([x, 0.021, zc + 2], [x + 0.55, 0.021, zc + 2], [x + 0.55, 0.021, zc - 2], [x, 0.021, zc - 2], [0, 0], [1, 0], [1, 1], [0, 1], white);
    }
  }
  const m = new THREE.Mesh(gb.build(), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.7 }));
  m.receiveShadow = true; scene.add(m);
}

// ---------------------------------------------------------------- Eiffel tower
{
  const g = new THREE.Group();
  const lat = new THREE.MeshStandardMaterial({ color: '#7a5236', alphaMap: texLattice, alphaTest: 0.5, transparent: false, side: THREE.DoubleSide, roughness: 0.7, metalness: 0.3, emissive: '#3a1c0c', emissiveIntensity: 0.4 });
  const solid = new THREE.MeshStandardMaterial({ color: '#6e4a30', roughness: 0.7, metalness: 0.3 });
  const prof = [[0, 50], [57, 30], [115, 17], [180, 9], [240, 5], [276, 3.2], [300, 0.6]];
  for (let k = 0; k < prof.length - 1; k++) {
    const [y0, h0] = prof[k], [y1, h1] = prof[k + 1];
    const geo = new THREE.CylinderGeometry(h1 * Math.SQRT2, h0 * Math.SQRT2, y1 - y0, 4, 1, true);
    geo.rotateY(Math.PI / 4);
    const uv = geo.attributes.uv;
    const reps = Math.max(1, Math.round((y1 - y0) / 14));
    for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 4 * Math.max(1, Math.round(h0 / 8)), uv.getY(i) * reps);
    const m = new THREE.Mesh(geo, lat); m.position.y = (y0 + y1) / 2; g.add(m);
  }
  // inner core, platforms, arch masks
  for (const [y, s, t] of [[57, 34, 4], [115, 20, 3], [276, 4.5, 3]]) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(s * 2, t, s * 2), solid); p.position.y = y; g.add(p);
  }
  const spire = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 1.5, 28, 6), solid); spire.position.y = 296; g.add(spire);
  // legs (thick corner members)
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const a = new THREE.Vector3(sx * 47, 0, sz * 47), b = new THREE.Vector3(sx * 16, 115, sz * 16);
    const leg = limb(a, b, 3.2, solid, 1.4); g.add(leg);
  }
  g.position.set(TOWER.x, 0, TOWER.z);
  g.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } });
  scene.add(g);
}

function limb(a, b, r, mat, r2 = null, seg = 20) {
  const d = new THREE.Vector3().subVectors(b, a); const len = d.length();
  const geo = new THREE.CylinderGeometry(r2 ?? r, r, len, seg);
  const m = new THREE.Mesh(geo, mat);
  m.position.copy(a).addScaledVector(d, 0.5);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
  return m;
}

// ---------------------------------------------------------------- instanced props
function instanced(geo, mat, n, shadow = true) {
  const m = new THREE.InstancedMesh(geo, mat, n);
  m.castShadow = shadow; m.receiveShadow = true;
  m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  scene.add(m);
  return m;
}
function vc(geo, hex) { // paint a geometry with a vertex color
  const c = col(hex); const n = geo.attributes.position.count; const a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[i * 3] = c.r; a[i * 3 + 1] = c.g; a[i * 3 + 2] = c.b; }
  geo.setAttribute('color', new THREE.BufferAttribute(a, 3));
  if (geo.index) return geo.toNonIndexed();
  return geo;
}
function prep(geo, hex, tx = 0, ty = 0, tz = 0, sx = 1, sy = 1, sz = 1) {
  geo.scale(sx, sy, sz); geo.translate(tx, ty, tz);
  if (geo.index) geo = geo.toNonIndexed();
  geo.deleteAttribute('uv');
  return vc(geo, hex);
}
const dummy = new THREE.Object3D();
const vcMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.8 });

// trees
const treeSpots = [];
for (const [zA, zB] of [[60, 990], [-1000, -60]]) {
  for (let z = zA; z < zB; z += 9) {
    if (zLines.some((l) => Math.abs(z - l.c) < 10)) continue;
    treeSpots.push([-12.4, z, R(0.9, 1.1)], [12.4, z, R(0.9, 1.1)]);
  }
}
for (let z = -36; z <= 36; z += 9) { treeSpots.push([-45, z, 1], [45, z, 1]); }
for (const x of [-30, -20, 20, 30]) { treeSpots.push([x, -37, 0.95], [x, 37, 0.95]); }
for (let z = -930; z < -470; z += 12) for (const x of [TOWER.x - 40, TOWER.x + 40]) treeSpots.push([x, z, R(0.9, 1.15)]);
{
  const trunk = prep(new THREE.CylinderGeometry(0.22, 0.32, 5.2, 7), '#a89b86', 0, 2.6, 0);
  const crowns = [];
  const cc = ['#5e7f3a', '#6b8c42', '#557532'];
  for (const [x, y, z, s] of [[0, 7.3, 0, 3.0], [1.4, 6.6, 0.8, 2.2], [-1.3, 6.8, -0.7, 2.3], [0.3, 8.6, -0.5, 2.0], [-0.6, 6.2, 1.4, 1.9]]) {
    crowns.push(prep(new THREE.IcosahedronGeometry(1, 1), pick(cc), x, y, z, s, s * 0.85, s));
  }
  const geo = mergeGeometries([trunk, ...crowns]);
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, flatShading: true });
  const trees = instanced(geo, mat, treeSpots.length);
  treeSpots.forEach(([x, z, s], i) => {
    dummy.position.set(x, 0.15, z); dummy.rotation.set(0, R(0, Math.PI * 2), 0); dummy.scale.set(s, s * R(0.92, 1.08), s);
    dummy.updateMatrix(); trees.setMatrixAt(i, dummy.matrix);
    trees.setColorAt(i, jitter(col('#ffffff'), 0.18));
  });
}

// street lamps
{
  const spots = [];
  for (const [zA, zB] of [[62, 990], [-1000, -62]]) for (let z = zA + 4.5; z < zB; z += 27) { if (zLines.some((l) => Math.abs(z - l.c) < 9)) continue; spots.push([-11, z], [11, z]); }
  for (const [x, z] of [[-24, -24], [24, -24], [-24, 24], [24, 24], [-12, 12], [14, 2], [-14, 2], [0, 14]]) spots.push([x, z]);
  const pole = prep(new THREE.CylinderGeometry(0.07, 0.12, 4.6, 8), '#1d2a24', 0, 2.3, 0);
  const base = prep(new THREE.CylinderGeometry(0.2, 0.26, 0.6, 8), '#1d2a24', 0, 0.3, 0);
  const lant = prep(new THREE.CylinderGeometry(0.22, 0.14, 0.55, 6), '#fff1cf', 0, 4.95, 0);
  const cap = prep(new THREE.ConeGeometry(0.3, 0.3, 6), '#1d2a24', 0, 5.35, 0);
  const lamps = instanced(mergeGeometries([pole, base, lant, cap]), vcMat, spots.length);
  spots.forEach(([x, z], i) => { dummy.position.set(x, 0.15, z); dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); lamps.setMatrixAt(i, dummy.matrix); });
}

// cars
const cars = [];
let carMesh;
{
  const body = prep(new THREE.BoxGeometry(4.3, 0.75, 1.85), '#ffffff', 0, 0.62, 0);
  const hood = prep(new THREE.BoxGeometry(4.1, 0.12, 1.75), '#ffffff', 0, 1.02, 0);
  const cab = prep(new THREE.BoxGeometry(2.3, 0.62, 1.62), '#2a3038', 0.15, 1.38, 0);
  const roof = prep(new THREE.BoxGeometry(2.0, 0.06, 1.55), '#ffffff', 0.15, 1.71, 0);
  const wheels = [];
  for (const x of [-1.35, 1.35]) for (const z of [-0.85, 0.85]) wheels.push(prep(new THREE.CylinderGeometry(0.34, 0.34, 0.24, 10).rotateX(Math.PI / 2), '#141414', x, 0.34, z));
  const hl = [prep(new THREE.BoxGeometry(0.06, 0.16, 0.4), '#fffbe8', 2.16, 0.8, 0.6), prep(new THREE.BoxGeometry(0.06, 0.16, 0.4), '#fffbe8', 2.16, 0.8, -0.6)];
  const tl = [prep(new THREE.BoxGeometry(0.06, 0.14, 0.4), '#d8261d', -2.16, 0.82, 0.6), prep(new THREE.BoxGeometry(0.06, 0.14, 0.4), '#d8261d', -2.16, 0.82, -0.6)];
  const geo = mergeGeometries([body, hood, cab, roof, ...wheels, ...hl, ...tl]);
  geo.rotateY(Math.PI / 2); // length along z, front toward -z
  const palette = ['#f2f2f0', '#c9ccd1', '#1c1d21', '#24365e', '#8f1f1f', '#5a5e66', '#f2f2f0', '#33473a', '#d9d2c1', '#1c1d21'];
  const lanes = [{ x: 1.75, dir: -1 }, { x: 5.25, dir: -1 }, { x: 8.6, dir: -1 }, { x: -1.75, dir: 1 }, { x: -5.25, dir: 1 }, { x: -8.6, dir: 1 }];
  for (const ln of lanes) {
    let z = R(60, 80);
    while (z < 1000) {
      cars.push({ x: ln.x + R(-0.15, 0.15), z0: z, dir: ln.dir, v: R(11, 16) * (ln.x === 8.6 || ln.x === -8.6 ? 0.7 : 1), color: col(pick(palette)) });
      z += R(14, 38);
    }
  }
  carMesh = instanced(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.35, metalness: 0.35 }), cars.length);
  cars.forEach((c, i) => carMesh.setColorAt(i, c.color));
}
function updateCars(t) {
  const span = 940;
  cars.forEach((c, i) => {
    let z = c.z0 + c.dir * c.v * t;
    z = 60 + ((((z - 60) % span) + span) % span);
    dummy.position.set(c.x, 0, z); dummy.rotation.set(0, c.dir > 0 ? Math.PI : 0, 0); dummy.scale.set(1, 1, 1);
    dummy.updateMatrix(); carMesh.setMatrixAt(i, dummy.matrix);
  });
  carMesh.instanceMatrix.needsUpdate = true;
}

// pedestrians
const peds = [];
let pedBody, pedHead, pedHair;
{
  // boulevard sidewalks
  for (let i = 0; i < 260; i++) {
    const side = rand() < 0.5 ? -1 : 1;
    peds.push({ x: side * R(11.6, 14.4), z: R(60, 990), dx: 0, dz: rand() < 0.5 ? -1 : 1, v: R(1.1, 1.6), wrap: [60, 990] });
  }
  // plaza walkers (avoid fountain & the man)
  let tries = 0;
  while (peds.length < 260 + 46 && tries++ < 5000) {
    const a = R(0, Math.PI * 2); const dx = Math.cos(a), dz = Math.sin(a);
    const x = R(-48, 48), z = R(-40, 40);
    const distLine = (P) => Math.abs((P.x - x) * dz - (P.z - z) * dx);
    if (distLine(FOUNTAIN) < 8.5 || distLine(MAN) < 2.0) continue;
    peds.push({ x, z, dx, dz, v: R(0.9, 1.5), plaza: true });
  }
  const bodyG = mergeGeometries([
    prep(new THREE.CapsuleGeometry(0.2, 0.55, 4, 10), '#ffffff', 0, 1.2, 0, 1.15, 1, 0.75),
    prep(new THREE.CylinderGeometry(0.075, 0.07, 0.85, 6), '#2b2f38', 0.1, 0.45, 0),
    prep(new THREE.CylinderGeometry(0.075, 0.07, 0.85, 6), '#2b2f38', -0.1, 0.45, 0),
    prep(new THREE.BoxGeometry(0.11, 0.08, 0.26), '#1a1a1a', 0.1, 0.04, -0.04),
    prep(new THREE.BoxGeometry(0.11, 0.08, 0.26), '#1a1a1a', -0.1, 0.04, -0.04),
  ]);
  const headG = prep(new THREE.SphereGeometry(0.11, 12, 10), '#ffffff', 0, 1.68, 0);
  const hairG = prep(new THREE.SphereGeometry(0.118, 12, 8, 0, Math.PI * 2, 0, Math.PI * 0.55), '#ffffff', 0, 1.7, 0.01);
  pedBody = instanced(bodyG, vcMat, peds.length);
  pedHead = instanced(headG, vcMat, peds.length);
  pedHair = instanced(hairG, vcMat, peds.length);
  const clothes = ['#23324f', '#7d2a2a', '#d9cdb5', '#2f2f33', '#576b4a', '#b8834a', '#e8e4dc', '#41566e', '#8a6f9c', '#c24d3a', '#1f1f22', '#9aa6ad'];
  const skins = ['#f1c9a5', '#e0ac85', '#c68b62', '#8d5a3b', '#5e3b26', '#f4d2b3'];
  const hairs = ['#1d1510', '#3a2618', '#6b4a2a', '#b88a4f', '#2b2b2b', '#9a9a9a', '#5a2d1a'];
  peds.forEach((p, i) => { pedBody.setColorAt(i, col(pick(clothes))); pedHead.setColorAt(i, col(pick(skins))); pedHair.setColorAt(i, col(pick(hairs))); p.phase = R(0, 10); });
}
function updatePeds(t) {
  peds.forEach((p, i) => {
    let x = p.x + p.dx * p.v * t, z = p.z + p.dz * p.v * t;
    if (p.wrap) { const s = p.wrap[1] - p.wrap[0]; z = p.wrap[0] + ((((z - p.wrap[0]) % s) + s) % s); }
    if (p.plaza) { // bounce inside plaza via triangle wave
      const tri = (v, a, b) => { const s = b - a; let u = ((v - a) % (2 * s) + 2 * s) % (2 * s); return a + (u > s ? 2 * s - u : u); };
      x = tri(x, -49, 49); z = tri(z, -41, 41);
    }
    const bob = Math.abs(Math.sin((t + p.phase) * 6.5)) * 0.05;
    const yaw = Math.atan2(-p.dx, -p.dz);
    dummy.position.set(x, 0.15 + bob, z); dummy.rotation.set(0, yaw, Math.sin((t + p.phase) * 6.5) * 0.03); dummy.scale.set(1, 1, 1); dummy.updateMatrix();
    pedBody.setMatrixAt(i, dummy.matrix); pedHead.setMatrixAt(i, dummy.matrix); pedHair.setMatrixAt(i, dummy.matrix);
  });
  pedBody.instanceMatrix.needsUpdate = pedHead.instanceMatrix.needsUpdate = pedHair.instanceMatrix.needsUpdate = true;
}

// plaza furniture: benches, café terrace, Morris column, fountain
{
  const wood = '#9a6a43', iron = '#1d2a24';
  const benchG = mergeGeometries([
    prep(new THREE.BoxGeometry(1.8, 0.07, 0.45), wood, 0, 0.45, 0),
    prep(new THREE.BoxGeometry(1.8, 0.4, 0.06), wood, 0, 0.75, 0.24),
    prep(new THREE.BoxGeometry(0.06, 0.45, 0.45), iron, -0.8, 0.22, 0),
    prep(new THREE.BoxGeometry(0.06, 0.45, 0.45), iron, 0.8, 0.22, 0),
  ]);
  const benchSpots = [];
  for (let k = 0; k < 6; k++) { const a = (k / 6) * Math.PI * 2 + 0.3; benchSpots.push([FOUNTAIN.x + Math.sin(a) * 9.2, FOUNTAIN.z + Math.cos(a) * 9.2, a]); }
  benchSpots.push([11, 9, -Math.PI / 2], [11, 4, -Math.PI / 2], [-11, 10, Math.PI / 2]);
  const benches = instanced(benchG, vcMat, benchSpots.length);
  benchSpots.forEach(([x, z, a], i) => { dummy.position.set(x, 0.15, z); dummy.rotation.set(0, a, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); benches.setMatrixAt(i, dummy.matrix); });

  // café terrace along the east side
  const tableG = mergeGeometries([
    prep(new THREE.CylinderGeometry(0.35, 0.35, 0.04, 16), '#d8d4cc', 0, 0.74, 0),
    prep(new THREE.CylinderGeometry(0.03, 0.03, 0.72, 6), '#222', 0, 0.37, 0),
    prep(new THREE.BoxGeometry(0.4, 0.04, 0.4), '#b4462e', 0.55, 0.45, 0), prep(new THREE.BoxGeometry(0.04, 0.42, 0.4), '#b4462e', 0.75, 0.66, 0),
    prep(new THREE.BoxGeometry(0.4, 0.04, 0.4), '#b4462e', -0.55, 0.45, 0), prep(new THREE.BoxGeometry(0.04, 0.42, 0.4), '#b4462e', -0.75, 0.66, 0),
    prep(new THREE.BoxGeometry(0.08, 0.06, 0.08), '#f5f1e8', 0.12, 0.79, 0.08), prep(new THREE.BoxGeometry(0.08, 0.06, 0.08), '#f5f1e8', -0.1, 0.79, -0.1),
  ]);
  const tSpots = [];
  for (let z = -34; z <= 34; z += 2.4) for (const x of [47.5, 49.8]) if (rand() < 0.85) tSpots.push([x + R(-0.2, 0.2), z + R(-0.2, 0.2)]);
  for (let x = -40; x <= -20; x += 2.4) for (const z of [-40.5]) tSpots.push([x, z]);
  const tables = instanced(tableG, vcMat, tSpots.length);
  tSpots.forEach(([x, z], i) => { dummy.position.set(x, 0.15, z); dummy.rotation.set(0, R(-0.3, 0.3), 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); tables.setMatrixAt(i, dummy.matrix); });

  // Morris column
  const mc = new THREE.Group();
  const green = new THREE.MeshStandardMaterial({ color: '#1f4a36', roughness: 0.6, metalness: 0.3 });
  const b1 = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.8, 0.5, 24), green); b1.position.y = 0.25;
  const b2 = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.62, 2.6, 24, 1, true), new THREE.MeshStandardMaterial({ map: texPoster, roughness: 0.8 })); b2.position.y = 1.8;
  const b3 = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.66, 0.25, 24), green); b3.position.y = 3.2;
  const dome = new THREE.Mesh(new THREE.SphereGeometry(0.62, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), green); dome.position.y = 3.3; dome.scale.y = 0.75;
  const fin = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.5, 8), green); fin.position.y = 4.0;
  mc.add(b1, b2, b3, dome, fin); mc.position.set(15, 0.15, 13);
  mc.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  scene.add(mc);
}

// fountain
const fountain = { jets: [], ripples: [] };
{
  const g = new THREE.Group();
  const stone = new THREE.MeshStandardMaterial({ color: '#d9cdb6', roughness: 0.75 });
  const water = new THREE.MeshStandardMaterial({ color: '#5aa7c7', roughness: 0.08, metalness: 0.2, emissive: '#1c5f7a', emissiveIntensity: 0.35 });
  const rim = new THREE.Mesh(new THREE.CylinderGeometry(5.6, 5.8, 0.7, 64), stone); rim.position.y = 0.35;
  const inner = new THREE.Mesh(new THREE.CylinderGeometry(5.15, 5.15, 0.2, 64), water); inner.position.y = 0.6;
  const ped = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 1.1, 1.6, 24), stone); ped.position.y = 1.3;
  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(2.3, 0.9, 0.55, 48), stone); bowl.position.y = 2.25;
  const bowlW = new THREE.Mesh(new THREE.CylinderGeometry(2.05, 2.05, 0.05, 48), water); bowlW.position.y = 2.5;
  const col2 = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, 1.3, 16), stone); col2.position.y = 3.1;
  const bowl2 = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.35, 0.3, 32), stone); bowl2.position.y = 3.8;
  g.add(rim, inner, ped, bowl, bowlW, col2, bowl2);
  // rim top lip
  const lip = new THREE.Mesh(new THREE.TorusGeometry(5.5, 0.18, 8, 64), stone); lip.rotation.x = Math.PI / 2; lip.position.y = 0.72; g.add(lip);
  const jetMat = new THREE.MeshStandardMaterial({ color: '#e6f6ff', transparent: true, opacity: 0.55, roughness: 0.05, emissive: '#9fd8f0', emissiveIntensity: 0.5, depthWrite: false });
  const top = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.12, 1.4, 10, 1, true), jetMat); top.position.y = 4.6; g.add(top); fountain.jets.push(top);
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2;
    const arc = new THREE.Mesh(new THREE.TorusGeometry(1.1, 0.05, 6, 20, Math.PI * 0.8), jetMat);
    arc.position.set(Math.sin(a) * 3.0, 0.6, Math.cos(a) * 3.0); arc.rotation.y = a + Math.PI / 2; arc.rotation.z = Math.PI * 0.1;
    g.add(arc); fountain.jets.push(arc);
  }
  const ripMat = new THREE.MeshBasicMaterial({ color: '#e8fbff', transparent: true, opacity: 0.4, depthWrite: false });
  for (let k = 0; k < 4; k++) { const r = new THREE.Mesh(new THREE.RingGeometry(0.95, 1, 64), ripMat.clone()); r.rotation.x = -Math.PI / 2; r.position.y = 0.71; g.add(r); fountain.ripples.push(r); }
  g.position.copy(FOUNTAIN);
  g.traverse((o) => { if (o.isMesh) { o.castShadow = o.material !== jetMat && !fountain.ripples.includes(o); o.receiveShadow = true; } });
  scene.add(g);
}
function updateFountain(t) {
  fountain.ripples.forEach((r, k) => { const u = ((t * 0.35 + k / 4) % 1); const s = 1.2 + u * 3.8; r.scale.set(s, s, 1); r.material.opacity = 0.45 * (1 - u); });
  fountain.jets[0].scale.y = 1 + Math.sin(t * 9) * 0.06;
}

// pigeons
const pigeons = [];
let pigeonMesh;
{
  const geo = mergeGeometries([
    prep(new THREE.SphereGeometry(1, 10, 8), '#8d929c', 0, 0.12, 0, 0.085, 0.075, 0.14),
    prep(new THREE.SphereGeometry(1, 8, 6), '#5d6672', 0, 0.2, -0.12, 0.045, 0.045, 0.05),
    prep(new THREE.SphereGeometry(1, 8, 6), '#4f6b6a', 0, 0.16, -0.08, 0.055, 0.05, 0.055),
    prep(new THREE.BoxGeometry(0.1, 0.02, 0.12), '#5b616b', 0, 0.12, 0.16),
    prep(new THREE.ConeGeometry(0.012, 0.04, 4).rotateX(-Math.PI / 2), '#d9a07a', 0, 0.2, -0.18),
    prep(new THREE.BoxGeometry(0.2, 0.025, 0.16), '#6f7581', 0, 0.15, 0.02),
  ]);
  for (let i = 0; i < 11; i++) {
    const a = R(0, Math.PI * 2), r = R(0.9, 2.6);
    pigeons.push({ x: MAN.x + Math.cos(a) * r, z: MAN.z - 0.6 + Math.sin(a) * r, yaw: R(0, Math.PI * 2), ph: R(0, 10), sp: R(2.5, 4.5) });
  }
  pigeonMesh = instanced(geo, vcMat, pigeons.length);
}
function updatePigeons(t) {
  pigeons.forEach((p, i) => {
    const peck = Math.max(0, Math.sin((t + p.ph) * p.sp)) ** 6;
    const hop = Math.max(0, Math.sin((t * 0.7 + p.ph) * 3.1)) ** 30 * 0.05;
    const step = Math.floor((t + p.ph) * 0.8);
    const yaw = p.yaw + step * 0.9;
    dummy.position.set(p.x + Math.sin(yaw) * 0.0, 0.15 + hop, p.z);
    dummy.rotation.set(0, 0, 0); dummy.rotation.y = yaw; dummy.rotateX(-peck * 0.6);
    dummy.scale.set(1, 1, 1); dummy.updateMatrix(); pigeonMesh.setMatrixAt(i, dummy.matrix);
  });
  pigeonMesh.instanceMatrix.needsUpdate = true;
}

// ---------------------------------------------------------------- the man on his phone
const man = { group: new THREE.Group() };
const screenCanvas = document.createElement('canvas'); screenCanvas.width = 400; screenCanvas.height = 820;
const screenCtx = screenCanvas.getContext('2d');
const screenTex = new THREE.CanvasTexture(screenCanvas); screenTex.colorSpace = THREE.SRGBColorSpace; screenTex.anisotropy = 8;
{
  const M = man.group;
  const skin = new THREE.MeshStandardMaterial({ color: '#d9a27e', roughness: 0.6 });
  const hoodie = new THREE.MeshStandardMaterial({ color: '#c8532d', roughness: 0.85 });
  const hoodieD = new THREE.MeshStandardMaterial({ color: '#a8421f', roughness: 0.9 });
  const jeans = new THREE.MeshStandardMaterial({ color: '#2c3b57', roughness: 0.85 });
  const shoe = new THREE.MeshStandardMaterial({ color: '#f2f1ec', roughness: 0.6 });
  const sole = new THREE.MeshStandardMaterial({ color: '#9a9690', roughness: 0.8 });
  const hair = new THREE.MeshStandardMaterial({ color: '#2a1b12', roughness: 0.75 });
  const bag = new THREE.MeshStandardMaterial({ color: '#1f2835', roughness: 0.7 });
  const bagD = new THREE.MeshStandardMaterial({ color: '#141a23', roughness: 0.7 });
  const white = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.3 });
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const add = (m, x, y, z) => { m.position.set(x, y, z); M.add(m); return m; };

  for (const s of [-1, 1]) {
    add(new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.08, 0.28), shoe), s * 0.11, 0.07, -0.04);
    add(new THREE.Mesh(new THREE.BoxGeometry(0.115, 0.03, 0.29), sole), s * 0.11, 0.015, -0.04);
    M.add(limb(V(s * 0.1, 0.93, 0.0), V(s * 0.11, 0.1, 0.0), 0.075, jeans, 0.085));
    M.add(limb(V(s * 0.21, 1.44, 0.02), V(s * 0.19, 1.16, -0.07), 0.062, hoodie));
    M.add(limb(V(s * 0.19, 1.16, -0.07), V(s * 0.075, 1.24, -0.29), 0.055, hoodie, 0.05));
    add(new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 10), hoodie), s * 0.19, 1.16, -0.07);
    add(new THREE.Mesh(new THREE.SphereGeometry(0.085, 24, 16), hoodie), s * 0.205, 1.44, 0.02);
    const hand = add(new THREE.Mesh(new THREE.SphereGeometry(0.036, 14, 12), skin), s * 0.055, 1.255, -0.312);
    hand.scale.set(0.75, 1.25, 0.85);
    const cuff = add(new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.05, 14), hoodieD), s * 0.082, 1.243, -0.27);
    cuff.rotation.x = 1.2; cuff.rotation.z = s * 0.5;
    // straps of the backpack
    const strap = add(new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.42, 0.03), bagD), s * 0.12, 1.3, -0.085);
    strap.rotation.x = 0.08;
  }
  add(new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.2, 0.22), jeans), 0, 0.97, 0);
  const torso = add(new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.36, 10, 32), hoodie), 0, 1.25, 0.0);
  torso.scale.set(1.28, 1, 0.78); man.torso = torso;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.06, 18), hoodieD), 0, 1.03, 0).scale.set(1, 1, 0.8);
  const hood = add(new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 12), hoodieD), 0, 1.5, 0.1); hood.scale.set(1.25, 0.55, 0.85);
  // backpack
  const bp = add(new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.42, 0.15), bag), 0, 1.24, 0.19);
  const flap = add(new THREE.Mesh(new THREE.BoxGeometry(0.33, 0.12, 0.16), bagD), 0, 1.42, 0.195);
  const pocket = add(new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.16, 0.05), bagD), 0, 1.12, 0.28);
  const tag = add(new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.03, 0.01), new THREE.MeshStandardMaterial({ color: '#f2c14e' })), 0.08, 1.2, 0.307);
  void bp; void flap; void pocket; void tag;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.055, 0.1, 12), skin), 0, 1.55, -0.01);

  // head
  const head = new THREE.Group(); head.position.set(0, 1.6, -0.02); head.rotation.x = -0.42; M.add(head); man.head = head;
  const skull = new THREE.Mesh(new THREE.SphereGeometry(0.105, 24, 18), skin); skull.scale.set(0.92, 1.08, 1); skull.position.y = 0.08; head.add(skull);
  const hairCap = new THREE.Mesh(new THREE.SphereGeometry(0.113, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.56), hair); hairCap.scale.set(0.95, 1.05, 1.06); hairCap.position.set(0, 0.095, 0.01); head.add(hairCap);
  const fringe = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 10), hair); fringe.scale.set(1.35, 0.45, 0.9); fringe.position.set(0, 0.165, -0.06); head.add(fringe);
  const crown = new THREE.Mesh(new THREE.SphereGeometry(0.06, 14, 10), hair); crown.scale.set(1.2, 0.5, 1.4); crown.position.set(0, 0.19, 0.0); head.add(crown);
  for (const s of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.SphereGeometry(0.025, 8, 8), skin); ear.position.set(s * 0.098, 0.075, 0.0); ear.scale.set(0.5, 1, 0.8); head.add(ear);
    const pod = new THREE.Mesh(new THREE.CapsuleGeometry(0.008, 0.02, 4, 8), white); pod.position.set(s * 0.104, 0.06, -0.005); head.add(pod);
  }
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.018, 8, 8), skin); nose.position.set(0, 0.06, -0.105); head.add(nose);

  // phone
  const phone = new THREE.Group(); phone.position.set(0, 1.285, -0.325); phone.rotation.x = -0.92; M.add(phone); man.phone = phone;
  const caseM = new THREE.Mesh(new THREE.BoxGeometry(0.076, 0.158, 0.009), new THREE.MeshStandardMaterial({ color: '#1a1b1e', roughness: 0.35, metalness: 0.5 }));
  phone.add(caseM);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.07, 0.152), new THREE.MeshBasicMaterial({ map: screenTex, toneMapped: false }));
  scr.position.z = 0.0047; phone.add(scr);
  const thumb = new THREE.Mesh(new THREE.CapsuleGeometry(0.0085, 0.03, 4, 8), skin); thumb.position.set(0.028, -0.035, 0.012); thumb.rotation.z = 0.7; phone.add(thumb); man.thumb = thumb;
  const glow = new THREE.PointLight('#a9c8ff', 0.035, 0.6, 2); glow.position.set(0, 0, 0.12); phone.add(glow);

  M.position.copy(MAN);
  M.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  scr.castShadow = false;
  scene.add(M);
}

// phone UI
const mapStreets = [];
for (let i = 0; i < 26; i++) mapStreets.push({ x0: R(-60, 460), y0: R(-60, 880), a: R(0, Math.PI), w: R(5, 16) });
function roundRect(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function drawScreen(t, dist) {
  const g = screenCtx, w = 400, h = 820;
  g.fillStyle = '#12151b'; g.fillRect(0, 0, w, h);
  // map
  g.save(); g.translate(0, 0);
  g.fillStyle = '#1b2029'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#1d3326'; g.beginPath(); g.ellipse(80, 640, 120, 70, 0.4, 0, Math.PI * 2); g.fill();
  g.strokeStyle = '#21486b'; g.lineWidth = 34; g.lineCap = 'round';
  g.beginPath(); g.moveTo(-40, 520); g.bezierCurveTo(120, 420, 240, 640, 460, 560); g.stroke();
  g.strokeStyle = '#2d3442'; g.lineCap = 'butt';
  for (const s of mapStreets) { g.lineWidth = s.w; g.beginPath(); g.moveTo(s.x0 - Math.cos(s.a) * 700, s.y0 - Math.sin(s.a) * 700); g.lineTo(s.x0 + Math.cos(s.a) * 700, s.y0 + Math.sin(s.a) * 700); g.stroke(); }
  g.strokeStyle = '#3a4356'; g.lineWidth = 22; g.beginPath(); g.moveTo(200, -20); g.lineTo(200, 840); g.stroke();
  g.lineWidth = 2; g.strokeStyle = '#53607a'; g.setLineDash([10, 10]); g.beginPath(); g.moveTo(200, -20); g.lineTo(200, 840); g.stroke(); g.setLineDash([]);
  g.restore();
  // user location
  const ux = 200, uy = 470;
  const pulse = (t * 0.9) % 1;
  g.fillStyle = `rgba(61,139,255,${0.35 * (1 - pulse)})`; g.beginPath(); g.arc(ux, uy, 16 + pulse * 46, 0, Math.PI * 2); g.fill();
  g.fillStyle = 'rgba(61,139,255,0.25)'; g.beginPath(); g.arc(ux, uy, 26, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#fff'; g.beginPath(); g.arc(ux, uy, 14, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#3d8bff'; g.beginPath(); g.arc(ux, uy, 10, 0, Math.PI * 2); g.fill();
  // drone icon approaching
  const k = clamp(dist / 60, 0, 1);
  const dx = ux + k * 20, dy = uy - 18 - k * 360;
  g.strokeStyle = 'rgba(255,90,70,0.6)'; g.lineWidth = 3; g.setLineDash([6, 8]); g.beginPath(); g.moveTo(dx, dy); g.lineTo(ux, uy); g.stroke(); g.setLineDash([]);
  g.save(); g.translate(dx, dy); g.rotate(t * 0.0);
  g.strokeStyle = '#ff5a46'; g.lineWidth = 5; g.beginPath(); g.moveTo(-14, -14); g.lineTo(14, 14); g.moveTo(14, -14); g.lineTo(-14, 14); g.stroke();
  for (const [px, py] of [[-14, -14], [14, -14], [-14, 14], [14, 14]]) { g.beginPath(); g.arc(px, py, 8, 0, Math.PI * 2); g.stroke(); }
  g.fillStyle = '#ff5a46'; g.fillRect(-6, -6, 12, 12);
  g.restore();
  // status bar
  g.fillStyle = '#fff'; g.font = '600 26px Inter'; g.textBaseline = 'middle';
  g.fillText('18:47', 28, 32);
  g.strokeStyle = '#fff'; g.lineWidth = 2; roundRect(g, w - 70, 22, 40, 20, 5); g.stroke(); g.fillRect(w - 66, 26, 26, 12); g.fillRect(w - 28, 28, 3, 8);
  for (let i = 0; i < 4; i++) g.fillRect(w - 130 + i * 9, 40 - i * 5, 6, 4 + i * 5);
  // notification
  const appear = smooth(8.8, 9.4, t);
  if (appear > 0) {
    const y = lerp(-140, 70, appear);
    g.fillStyle = 'rgba(44,48,58,0.94)'; roundRect(g, 16, y, w - 32, 128, 26); g.fill();
    const ig = g.createLinearGradient(36, y + 22, 96, y + 82); ig.addColorStop(0, '#ff7a45'); ig.addColorStop(1, '#ff3d6e');
    g.fillStyle = ig; roundRect(g, 34, y + 26, 60, 60, 15); g.fill();
    g.strokeStyle = '#fff'; g.lineWidth = 4; g.beginPath(); g.moveTo(50, y + 42); g.lineTo(78, y + 70); g.moveTo(78, y + 42); g.lineTo(50, y + 70); g.stroke();
    for (const [px, py] of [[50, 42], [78, 42], [50, 70], [78, 70]]) { g.beginPath(); g.arc(px, y + py, 6, 0, Math.PI * 2); g.stroke(); }
    g.fillStyle = '#fff'; g.font = '700 24px Inter'; g.fillText('Drone à proximité', 110, y + 44);
    g.fillStyle = 'rgba(255,255,255,0.75)'; g.font = '500 21px Inter'; g.fillText(`${dist.toFixed(1).replace('.', ',')} m au-dessus de vous`, 110, y + 78);
    g.fillStyle = 'rgba(255,255,255,0.45)'; g.font = '500 17px Inter'; g.fillText('maintenant', w - 128, y + 30);
  }
  // bottom sheet
  g.fillStyle = 'rgba(28,31,38,0.96)'; roundRect(g, 0, h - 190, w, 210, 30); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.3)'; roundRect(g, w / 2 - 30, h - 176, 60, 6, 3); g.fill();
  g.fillStyle = '#fff'; g.font = '700 30px Inter'; g.fillText('Paris', 30, h - 132);
  g.fillStyle = 'rgba(255,255,255,0.6)'; g.font = '500 20px Inter'; g.fillText('Place du Marché · 18°C', 30, h - 96);
  g.fillStyle = '#3d8bff'; roundRect(g, 30, h - 70, 160, 46, 23); g.fill();
  g.fillStyle = '#fff'; g.font = '600 20px Inter'; g.fillText('Itinéraire', 64, h - 46);
  g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 2; roundRect(g, 204, h - 70, 160, 46, 23); g.stroke();
  g.fillStyle = '#fff'; g.fillText('Partager', 244, h - 46);
  // home indicator
  g.fillStyle = 'rgba(255,255,255,0.8)'; roundRect(g, w / 2 - 70, h - 14, 140, 6, 3); g.fill();
  screenTex.needsUpdate = true;
}
function updateMan(t) {
  const br = Math.sin(t * 1.9) * 0.012;
  man.torso.scale.set(1.28 + br, 1, 0.78 + br);
  man.head.rotation.x = -0.42 + Math.sin(t * 0.7) * 0.03;
  man.head.rotation.y = Math.sin(t * 0.45) * 0.04;
  const sw = (t * 1.3) % 1; const s = smooth(0, 0.35, sw) - smooth(0.5, 0.9, sw);
  man.thumb.position.y = -0.04 + s * 0.04;
  man.phone.rotation.z = Math.sin(t * 0.8) * 0.02;
}

// ---------------------------------------------------------------- sky + lighting
const sunDir = new THREE.Vector3(0.58, 0.36, -0.73).normalize();
const sky = new THREE.Mesh(new THREE.SphereGeometry(3000, 48, 24), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { sunDir: { value: sunDir } },
  vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `varying vec3 vDir; uniform vec3 sunDir;
    void main(){
      float h = vDir.y;
      vec3 hor = vec3(1.0, 0.80, 0.63), mid = vec3(0.70, 0.80, 0.92), top = vec3(0.33, 0.52, 0.80);
      vec3 c = mix(hor, mid, smoothstep(0.0, 0.2, h));
      c = mix(c, top, smoothstep(0.2, 0.75, h));
      float s = max(dot(normalize(vDir), sunDir), 0.0);
      c += vec3(1.0, 0.72, 0.42) * pow(s, 6.0) * 0.5 + vec3(1.0, 0.92, 0.75) * pow(s, 900.0) * 6.0;
      if (h < 0.0) c = hor * 0.97;
      gl_FragColor = vec4(pow(c, vec3(2.2)), 1.0);
    }`,
}));
sky.renderOrder = -1; scene.add(sky);

// soft stylised clouds
{
  const cloudMat = new THREE.MeshStandardMaterial({ color: '#fff2e4', roughness: 1, emissive: '#f7c9a4', emissiveIntensity: 0.35, flatShading: true });
  for (let i = 0; i < 26; i++) {
    const cg = new THREE.Group();
    const n = 4 + Math.floor(rand() * 5);
    for (let k = 0; k < n; k++) { const s = R(30, 70); const b = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 1), cloudMat); b.position.set(k * R(35, 55), R(-8, 15), R(-20, 20)); b.scale.y = 0.45; cg.add(b); }
    const a = R(-Math.PI * 0.9, Math.PI * 0.1);
    const d = R(1300, 2100);
    cg.position.set(Math.sin(a) * d * 0.9, R(380, 700), -Math.abs(Math.cos(a)) * d + R(-200, 600));
    cg.rotation.y = R(0, Math.PI);
    scene.add(cg);
  }
}

const hemi = new THREE.HemisphereLight('#bcd4ef', '#8a7058', 1.25); scene.add(hemi);
const sun = new THREE.DirectionalLight('#ffd6a8', 3.4);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
sun.shadow.camera.near = 1; sun.shadow.camera.far = 1200;
scene.add(sun); scene.add(sun.target);
const ambientFill = new THREE.DirectionalLight('#9fb6d6', 0.35); ambientFill.position.set(-0.6, 0.5, 0.6); scene.add(ambientFill);

const lightUp0 = new THREE.Vector3(0, 1, 0);
const lightRight = new THREE.Vector3().crossVectors(lightUp0, sunDir).normalize();
const lightUp = new THREE.Vector3().crossVectors(sunDir, lightRight).normalize();
function placeSun(focus, ext) {
  const texel = (2 * ext) / 4096;
  const fr = Math.round(focus.dot(lightRight) / texel) * texel;
  const fu = Math.round(focus.dot(lightUp) / texel) * texel;
  const fd = focus.dot(sunDir);
  const f = new THREE.Vector3().addScaledVector(lightRight, fr).addScaledVector(lightUp, fu).addScaledVector(sunDir, fd);
  sun.target.position.copy(f);
  sun.position.copy(f).addScaledVector(sunDir, 500);
  const c = sun.shadow.camera;
  c.left = -ext; c.right = ext; c.top = ext; c.bottom = -ext; c.updateProjectionMatrix();
  sun.target.updateMatrixWorld();
}

// ---------------------------------------------------------------- camera path
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const KEYS = [
  { t: 0.0, p: V3(46, 118, 960), q: V3(0, 14, 760), fov: 62 },
  { t: 1.35, p: V3(5, 16, 795), q: V3(0, 9, 650), fov: 78 },
  { t: 2.6, p: V3(-5, 9.5, 655), q: V3(1.5, 8, 505), fov: 86 },
  { t: 3.85, p: V3(5, 11.5, 505), q: V3(-1.5, 9, 355), fov: 86 },
  { t: 5.1, p: V3(-3.5, 9, 350), q: V3(0, 10, 200), fov: 84 },
  { t: 6.3, p: V3(0, 14, 200), q: V3(2, 5, 50), fov: 78 },
  { t: 7.3, p: V3(3, 32, 92), q: V3(6, 0, 14), fov: 64 },
  { t: 8.35, p: V3(7.15, 40, 18), q: V3(7, 0.5, 5.8), fov: 52 },
  { t: 9.4, p: V3(7.2, 17, 9.6), q: V3(7, 1.0, 5.75), fov: 46 },
  { t: 10.3, p: V3(7.4, 6.2, 7.7), q: V3(7.02, 1.2, 5.7), fov: 40 },
  { t: 11.15, p: V3(7.36, 3.5, 6.65), q: V3(7.02, 1.28, 5.7), fov: 31 },
  { t: 12.0, p: V3(7.43, 2.72, 6.3), q: V3(7.03, 1.3, 5.7), fov: 27, still: true },
];
function hermite(get, t) {
  const n = KEYS.length;
  let i = 0; while (i < n - 2 && t > KEYS[i + 1].t) i++;
  const k0 = KEYS[i], k1 = KEYS[i + 1];
  const tan = (j) => {
    const k = KEYS[j];
    if (k.still) return get(k).clone().multiplyScalar(0);
    if (j === 0) return get(KEYS[1]).clone().sub(get(KEYS[0])).multiplyScalar(1 / (KEYS[1].t - KEYS[0].t));
    if (j === n - 1) return get(KEYS[j]).clone().sub(get(KEYS[j - 1])).multiplyScalar(1 / (KEYS[j].t - KEYS[j - 1].t));
    return get(KEYS[j + 1]).clone().sub(get(KEYS[j - 1])).multiplyScalar(1 / (KEYS[j + 1].t - KEYS[j - 1].t));
  };
  const h = k1.t - k0.t, s = clamp((t - k0.t) / h, 0, 1);
  const s2 = s * s, s3 = s2 * s;
  const h00 = 2 * s3 - 3 * s2 + 1, h10 = s3 - 2 * s2 + s, h01 = -2 * s3 + 3 * s2, h11 = s3 - s2;
  return get(k0).clone().multiplyScalar(h00).addScaledVector(tan(i), h10 * h).addScaledVector(get(k1), h01).addScaledVector(tan(i + 1), h11 * h);
}
const fovV = (k) => new THREE.Vector3(k.fov, 0, 0);
function camState(t) {
  const p = hermite((k) => k.p, t), q = hermite((k) => k.q, t);
  return { p, q, fov: hermite(fovV, t).x };
}

let lastSpeed = 0;
function updateCamera(t) {
  const { p, q, fov } = camState(t);
  const dt = 1 / 120;
  const pa = camState(Math.max(0, t - dt)).p, pb = camState(Math.min(DURATION, t + dt)).p;
  const vel = pb.clone().sub(pa).multiplyScalar(1 / (2 * dt));
  const acc = pb.clone().add(pa).sub(p.clone().multiplyScalar(2)).multiplyScalar(1 / (dt * dt));
  const speed = vel.length(); lastSpeed = speed;
  const fwd = q.clone().sub(p).normalize();
  const right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize();
  const lateral = acc.dot(right);
  const fast = smooth(10, 80, speed);
  // drone-like shake
  const sh = fast * 0.12 + 0.015;
  p.x += (Math.sin(t * 13.1) * 0.6 + Math.sin(t * 29.7) * 0.4) * sh;
  p.y += (Math.sin(t * 11.3 + 1) * 0.6 + Math.sin(t * 23.9) * 0.4) * sh;
  camera.position.copy(p);
  const topDown = smooth(7.3, 8.3, t);
  camera.up.set(0, 1 - topDown, -topDown).normalize();
  camera.lookAt(q);
  const roll = clamp(-lateral * 0.006, -0.35, 0.35) * smooth(0.6, 1.2, t) * (1 - smooth(7.0, 8.0, t));
  camera.rotateZ(roll);
  camera.fov = fov;
  camera.near = clamp((p.y - 1.3) * 0.03, 0.02, 0.6);
  camera.updateProjectionMatrix();
  return { speed, fwd, vel };
}

// ---------------------------------------------------------------- post FX
const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
composer.setPixelRatio(1); composer.setSize(W, H);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.32, 0.6, 0.88);
composer.addPass(bloom);
composer.addPass(new OutputPass());
const finalPass = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uBlur: { value: 0 }, uCA: { value: 0.002 }, uTime: { value: 0 }, uRes: { value: new THREE.Vector2(W, H) }, uFlash: { value: 0 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uBlur, uCA, uTime, uFlash; uniform vec2 uRes; varying vec2 vUv;
    float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
    void main(){
      vec2 c = vec2(0.5, 0.52);
      vec2 d = vUv - c;
      float r = length(d * vec2(uRes.x/uRes.y, 1.0));
      vec3 acc = vec3(0.0); float wsum = 0.0;
      float jit = hash(vUv * uRes + uTime) ;
      for (int i = 0; i < 10; i++) {
        float f = (float(i) + jit) / 10.0;
        float sc = 1.0 - uBlur * f * smoothstep(0.05, 0.5, r);
        float ca = uCA * (0.5 + r * 2.0);
        vec3 s;
        s.r = texture2D(tDiffuse, c + d * sc * (1.0 + ca)).r;
        s.g = texture2D(tDiffuse, c + d * sc).g;
        s.b = texture2D(tDiffuse, c + d * sc * (1.0 - ca)).b;
        float w = 1.0 - f * 0.6;
        acc += s * w; wsum += w;
      }
      vec3 col = acc / wsum;
      float l = dot(col, vec3(0.299, 0.587, 0.114));
      col = mix(col, col * col * (3.0 - 2.0 * col), 0.22);
      col += vec3(-0.012, 0.004, 0.02) * (1.0 - l) + vec3(0.02, 0.008, -0.015) * l;
      col = mix(vec3(l), col, 1.08);
      float vig = smoothstep(1.05, 0.25, length(d * vec2(1.0, 0.85)) * 1.25);
      col *= mix(0.62, 1.0, vig);
      col += (hash(vUv * uRes + fract(uTime * 7.13)) - 0.5) * 0.035;
      col = mix(col, vec3(1.0), uFlash);
      gl_FragColor = vec4(col, 1.0);
    }`,
});
composer.addPass(finalPass);

// ---------------------------------------------------------------- HUD overlay (motion design layer)
const LAT0 = 48.85660, LON0 = 2.35220;
function drawHUD(g, t, st) {
  const s = W / 1080; const w = 1080, h = H / s;
  g.save(); g.scale(s, s);
  const hudA = smooth(0.4, 1.0, t);
  const white = (a) => `rgba(255,255,255,${a * hudA})`;
  g.lineWidth = 3; g.strokeStyle = white(0.85);
  const m = 56, L = 70;
  for (const [x, y, sx, sy] of [[m, m, 1, 1], [w - m, m, -1, 1], [m, h - m, 1, -1], [w - m, h - m, -1, -1]]) {
    g.beginPath(); g.moveTo(x, y + sy * L); g.lineTo(x, y); g.lineTo(x + sx * L, y); g.stroke();
  }
  g.textBaseline = 'middle';
  // REC + timecode
  if (Math.floor(t * 2) % 2 === 0) { g.fillStyle = `rgba(255,59,48,${hudA})`; g.beginPath(); g.arc(m + 34, m + 46, 11, 0, Math.PI * 2); g.fill(); }
  g.fillStyle = white(0.95); g.font = '600 30px Inter'; g.fillText('REC', m + 56, m + 47);
  const fr = Math.floor(t * FPS) % FPS, sec = Math.floor(t);
  g.font = '500 28px Inter'; g.fillText(`00:00:${String(sec).padStart(2, '0')}:${String(fr).padStart(2, '0')}`, m + 128, m + 47);
  g.textAlign = 'right'; g.fillText('DRONE · CAM 01', w - m - 24, m + 47);
  g.font = '500 22px Inter'; g.fillStyle = white(0.6); g.fillText('4K  ·  30 FPS  ·  ND16', w - m - 24, m + 84);
  g.textAlign = 'left';
  // compass strip
  const heading = (Math.atan2(st.fwd.x, -st.fwd.z) * 180 / Math.PI + 360) % 360;
  const cy = m + 140; const cx = w / 2; const span = 360;
  g.save(); g.beginPath(); g.rect(cx - span, cy - 40, span * 2, 80); g.clip();
  for (let d = -60; d <= 420; d += 5) {
    const x = cx + ((d - heading + 540) % 360 - 180) * 6;
    const big = d % 45 === 0;
    const fade = 1 - Math.abs(x - cx) / span;
    g.strokeStyle = white(0.7 * fade); g.lineWidth = big ? 3 : 2;
    g.beginPath(); g.moveTo(x, cy - (big ? 16 : 8)); g.lineTo(x, cy + (big ? 16 : 8)); g.stroke();
    if (big && d >= 0 && d < 360) { const lab = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'][d / 45]; g.fillStyle = white(0.9 * fade); g.font = '600 24px Inter'; g.textAlign = 'center'; g.fillText(lab, x, cy - 34 + 70); }
  }
  g.restore(); g.textAlign = 'center';
  g.fillStyle = white(0.95); g.beginPath(); g.moveTo(cx, cy - 26); g.lineTo(cx - 9, cy - 40); g.lineTo(cx + 9, cy - 40); g.fill();
  g.font = '600 22px Inter'; g.fillText(`${heading.toFixed(0).padStart(3, '0')}°`, cx, cy - 58);
  g.textAlign = 'left';

  // altitude ladder (right)
  const alt = camera.position.y;
  const lx = w - m - 30, ly = h / 2;
  g.save(); g.beginPath(); g.rect(lx - 80, ly - 260, 120, 520); g.clip();
  for (let a = Math.floor(alt) - 30; a <= alt + 30; a++) {
    const y = ly - (a - alt) * 16; const big = a % 5 === 0;
    const fade = 1 - Math.abs(y - ly) / 260;
    g.strokeStyle = white(0.7 * fade); g.lineWidth = 2;
    g.beginPath(); g.moveTo(lx, y); g.lineTo(lx - (big ? 26 : 12), y); g.stroke();
    if (big && a >= 0) { g.fillStyle = white(0.75 * fade); g.font = '500 20px Inter'; g.textAlign = 'right'; g.fillText(String(a), lx - 34, y); }
  }
  g.restore(); g.textAlign = 'left';
  g.fillStyle = white(0.95); g.beginPath(); g.moveTo(lx + 4, ly); g.lineTo(lx + 18, ly - 9); g.lineTo(lx + 18, ly + 9); g.fill();

  // speed ladder (left)
  const kmh = st.speed * 3.6;
  const sx = m + 30;
  g.save(); g.beginPath(); g.rect(sx - 40, ly - 260, 140, 520); g.clip();
  for (let v = Math.floor(kmh / 10) * 10 - 150; v <= kmh + 150; v += 10) {
    const y = ly - (v - kmh) * 1.7; const big = v % 50 === 0;
    const fade = 1 - Math.abs(y - ly) / 260;
    g.strokeStyle = white(0.7 * fade); g.lineWidth = 2;
    g.beginPath(); g.moveTo(sx, y); g.lineTo(sx + (big ? 26 : 12), y); g.stroke();
    if (big && v >= 0) { g.fillStyle = white(0.75 * fade); g.font = '500 20px Inter'; g.fillText(String(v), sx + 34, y); }
  }
  g.restore();
  g.fillStyle = white(0.95); g.beginPath(); g.moveTo(sx - 4, ly); g.lineTo(sx - 18, ly - 9); g.lineTo(sx - 18, ly + 9); g.fill();

  // bottom telemetry
  const by = h - m - 120;
  g.font = '500 22px Inter'; g.fillStyle = white(0.6);
  g.fillText('ALT', m + 24, by); g.fillText('VIT', m + 220, by); g.fillText('DIST. SOL', m + 420, by);
  g.font = '700 46px Inter'; g.fillStyle = white(0.97);
  g.fillText(`${alt.toFixed(1).replace('.', ',')} m`, m + 24, by + 46);
  g.fillText(`${Math.round(kmh)}`, m + 220, by + 46);
  g.font = '500 22px Inter'; g.fillStyle = white(0.7); g.fillText('km/h', m + 220 + g.measureText(`${Math.round(kmh)}`).width * 2.2 + 8, by + 54);
  const dGround = Math.max(0, alt - 1.8);
  g.font = '700 46px Inter'; g.fillStyle = white(0.97); g.fillText(`${dGround.toFixed(1).replace('.', ',')} m`, m + 420, by + 46);
  const lat = LAT0 - camera.position.z / 111320, lon = LON0 + camera.position.x / 73300;
  g.font = '500 22px Inter'; g.fillStyle = white(0.65);
  g.fillText(`${lat.toFixed(5)}° N   ${lon.toFixed(5)}° E   ·   PARIS, FR`, m + 24, by + 98);

  // center reticle (flight)
  const ret = 1 - smooth(7.6, 8.4, t);
  if (ret > 0) {
    g.strokeStyle = white(0.8 * ret); g.lineWidth = 2.5;
    const c = { x: w / 2, y: h / 2 };
    g.beginPath(); g.arc(c.x, c.y, 34, 0, Math.PI * 2); g.stroke();
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { g.beginPath(); g.moveTo(c.x + dx * 46, c.y + dy * 46); g.lineTo(c.x + dx * 72, c.y + dy * 72); g.stroke(); }
    g.fillStyle = white(0.9 * ret); g.beginPath(); g.arc(c.x, c.y, 3.5, 0, Math.PI * 2); g.fill();
  }
  // target lock on the man
  const lock = smooth(7.9, 8.6, t);
  if (lock > 0) {
    const head = new THREE.Vector3(MAN.x, 1.4, MAN.z - 0.12).project(camera);
    let tx = (head.x * 0.5 + 0.5) * w, ty = (-head.y * 0.5 + 0.5) * h;
    const follow = smooth(10.6, 11.6, t);
    tx = lerp(tx, w / 2, follow * 0.0);
    const size = lerp(420, 190, lock) * (1 + smooth(10.4, 11.4, t) * 1.9);
    const a = lock * (1 - smooth(11.2, 11.8, t));
    if (a > 0.01) {
      g.strokeStyle = `rgba(255,214,90,${a})`; g.lineWidth = 4;
      const hs = size / 2, cl = size * 0.22;
      for (const [sx2, sy2] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
        g.beginPath(); g.moveTo(tx + sx2 * hs, ty + sy2 * (hs - cl)); g.lineTo(tx + sx2 * hs, ty + sy2 * hs); g.lineTo(tx + sx2 * (hs - cl), ty + sy2 * hs); g.stroke();
      }
      g.fillStyle = `rgba(255,214,90,${a})`;
      g.beginPath(); g.arc(tx, ty, 5, 0, Math.PI * 2); g.fill();
      g.font = '700 26px Inter';
      const blink = Math.floor(t * 6) % 2 === 0 || t > 8.9;
      if (blink) g.fillText('SUJET VERROUILLÉ', tx - hs, ty - hs - 26);
      g.font = '500 22px Inter';
      const dist = camera.position.distanceTo(new THREE.Vector3(MAN.x, 1.7, MAN.z));
      g.fillText(`${dist.toFixed(1).replace('.', ',')} m  ·  ZOOM x${clamp(40 / dist, 1, 24).toFixed(1).replace('.', ',')}`, tx - hs, ty + hs + 30);
    }
  }
  g.restore();

  // opening title
  const ta = smooth(0.0, 0.25, t) * (1 - smooth(1.5, 2.0, t));
  if (ta > 0) {
    g.save(); g.scale(s, s);
    g.textAlign = 'center';
    const spread = lerp(46, 70, smooth(0, 2, t));
    g.font = '800 170px Inter';
    g.fillStyle = `rgba(255,255,255,${ta})`;
    g.shadowColor = 'rgba(0,0,0,0.35)'; g.shadowBlur = 30;
    const word = 'PARIS'; let total = 0; const ws = [...word].map((ch) => { const ww = g.measureText(ch).width; total += ww; return ww; });
    total += spread * (word.length - 1);
    let x = w / 2 - total / 2;
    [...word].forEach((ch, i) => { g.textAlign = 'left'; g.fillText(ch, x, h * 0.4); x += ws[i] + spread; });
    g.shadowBlur = 0; g.textAlign = 'center';
    g.font = '500 34px Inter'; g.fillStyle = `rgba(255,255,255,${ta * 0.9})`;
    g.fillText('48°51′24″N   2°21′08″E', w / 2, h * 0.4 + 110);
    g.fillStyle = `rgba(255,255,255,${ta * 0.8})`; g.fillRect(w / 2 - 60 * ta, h * 0.4 + 60, 120 * ta, 3);
    g.restore();
  }
}

// ---------------------------------------------------------------- frame
function update(t) {
  const st = updateCamera(t);
  sky.position.copy(camera.position);
  updateCars(t); updatePeds(t); updatePigeons(t); updateFountain(t); updateMan(t);
  const dist = camera.position.distanceTo(new THREE.Vector3(MAN.x, 1.7, MAN.z));
  drawScreen(t, dist);
  // shadow frustum follows the camera
  const alt = camera.position.y;
  const ext = t < 7.0 ? 170 : clamp(alt * 2.4 + 6, 7, 170);
  const focus = t < 7.0
    ? camera.position.clone().addScaledVector(new THREE.Vector3(st.fwd.x, 0, st.fwd.z).normalize(), 110).setY(0)
    : new THREE.Vector3(lerp(camera.position.x, MAN.x, 0.7), 0, lerp(camera.position.z, MAN.z, 0.7));
  placeSun(focus, ext);
  finalPass.uniforms.uBlur.value = smooth(25, 120, st.speed) * 0.055 + smooth(7.9, 9.5, t) * (1 - smooth(10.6, 11.4, t)) * 0.03;
  finalPass.uniforms.uCA.value = 0.0015 + smooth(25, 120, st.speed) * 0.004;
  finalPass.uniforms.uTime.value = t;
  return st;
}

window.renderFrame = (i, fmt = 'image/png') => {
  const t = i / FPS;
  const st = update(t);
  composer.render();
  out2d.drawImage(renderer.domElement, 0, 0, W, H);
  drawHUD(out2d, t, st);
  return outCanvas.toDataURL(fmt, 0.95);
};

await document.fonts.load('700 40px Inter');
await document.fonts.load('500 40px Inter');
await document.fonts.load('800 40px Inter');
window.STATS = { buildings: buildingCount, meshes: cityGroup.children.length };
window.READY = true;
