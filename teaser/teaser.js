import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { BokehPass } from "three/addons/postprocessing/BokehPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const W = 1920, H = 1080;
// ─── helpers ───
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lin = (t, a, b) => clamp((t - a) / (b - a));
const sm = (x) => x * x * (3 - 2 * x);
const eOut = (x) => 1 - Math.pow(1 - x, 3);
const eIn = (x) => x * x * x;
const eBack = (x) => { const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const mix = (a, b, x) => a + (b - a) * x;
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hot = (hex, k) => new THREE.Color(hex).multiplyScalar(k);

// ─── plans ───
const S = { s1: [0, 3.6], s2: [3.6, 7.6], s3: [7.6, 11.6], s4: [11.6, 15.0], s5: [15.0, 17.2], s6: [17.2, 20.0] };
const CUTS = [3.6, 7.6, 11.6, 15.0, 17.2];

// ─── renderer / post ───
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("c"), antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
const pmrem = new THREE.PMREMGenerator(renderer);
const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.PerspectiveCamera(40, W / H, 0.1, 400);
const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(new THREE.Scene(), camera);
const bokeh = new BokehPass(new THREE.Scene(), camera, { focus: 6, aperture: 0.002, maxblur: 0.01 });
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.8, 0.6, 0.85);
const finalPass = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uCA: { value: 0.004 }, uFlash: { value: 0 }, uFade: { value: 0 }, uTime: { value: 0 }, uVig: { value: 0.55 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float uCA, uFlash, uFade, uTime, uVig; varying vec2 vUv;
    float rnd(vec2 c){ return fract(sin(dot(c, vec2(12.9898,78.233))) * 43758.5453); }
    void main(){
      vec2 d = vUv - 0.5; float r = length(d);
      vec2 off = d * uCA * (0.5 + 2.0*r);
      vec3 col = vec3(texture2D(tDiffuse, vUv + off).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - off).b);
      col *= 1.0 - uVig * smoothstep(0.3, 0.95, r);
      col += (rnd(vUv * 1731.0 + uTime) - 0.5) * 0.055;
      col = mix(col, vec3(1.0, 0.97, 0.92), uFlash);
      col *= 1.0 - uFade;
      gl_FragColor = vec4(col, 1.0);
    }`
});
composer.addPass(renderPass);
composer.addPass(bokeh);
composer.addPass(bloom);
composer.addPass(new OutputPass());
composer.addPass(finalPass);

// ─── textures canvas ───
function circuitTextures(seed) {
  const r = rng(seed), N = 1024;
  const c1 = document.createElement("canvas"), c2 = document.createElement("canvas");
  c1.width = c2.width = c1.height = c2.height = N;
  const a = c1.getContext("2d"), e = c2.getContext("2d");
  a.fillStyle = "#081326"; a.fillRect(0, 0, N, N);
  e.fillStyle = "#000"; e.fillRect(0, 0, N, N);
  const blues = ["#0d1f3d", "#12305a", "#1a4478", "#0a1830", "#233a5e", "#2c5796", "#101a2c"];
  for (let i = 0; i < 420; i++) {
    const w = 8 + r() ** 2 * 220, h = 8 + r() ** 2 * 160, x = r() * N, y = r() * N;
    a.fillStyle = blues[Math.floor(r() * blues.length)]; a.fillRect(x, y, w, h);
    if (r() < 0.35) { a.strokeStyle = "rgba(120,170,255,.25)"; a.strokeRect(x + 2, y + 2, w - 4, h - 4); }
    if (r() < 0.25) { for (let k = 0; k < w / 10; k++) { a.fillStyle = "#6e7f99"; a.fillRect(x + k * 10, y - 6, 5, 6); } }
  }
  a.strokeStyle = "rgba(90,140,220,.35)"; a.lineWidth = 2;
  for (let i = 0; i < 160; i++) {
    let x = r() * N, y = r() * N; a.beginPath(); a.moveTo(x, y);
    for (let k = 0; k < 4; k++) { if (r() < .5) x += (r() - .5) * 300; else y += (r() - .5) * 300; a.lineTo(x, y); }
    a.stroke();
  }
  for (let i = 0; i < 140; i++) {
    const x = r() * N, y = r() * N, s = 3 + r() * 9;
    const col = r() < 0.12 ? "#ff9a3a" : r() < 0.5 ? "#7fc4ff" : "#e8f3ff";
    a.fillStyle = col; a.fillRect(x, y, s, s * (r() < .5 ? 1 : 3));
    e.fillStyle = col; e.fillRect(x, y, s, s * (r() < .5 ? 1 : 3));
  }
  const t1 = new THREE.CanvasTexture(c1), t2 = new THREE.CanvasTexture(c2);
  t1.colorSpace = t2.colorSpace = THREE.SRGBColorSpace;
  t1.anisotropy = 8;
  return [t1, t2];
}

function slabLabel(name, num, color) {
  const c = document.createElement("canvas"); c.width = 720; c.height = 1020;
  const g = c.getContext("2d");
  g.clearRect(0, 0, c.width, c.height);
  g.strokeStyle = "rgba(255,255,255,.9)"; g.lineWidth = 6; g.strokeRect(34, 34, 652, 952);
  g.fillStyle = "rgba(255,255,255,.95)"; g.font = "600 44px 'Exo 2'"; g.textAlign = "left";
  g.fillText(num, 70, 110);
  g.font = "150px Anton"; g.textAlign = "center"; g.fillText(name, 360, 900);
  // traces de griffes
  g.strokeStyle = "rgba(255,255,255,.85)"; g.lineCap = "round";
  for (let i = 0; i < 3; i++) {
    g.lineWidth = 26 - i * 3; g.beginPath();
    g.moveTo(230 + i * 95, 250); g.quadraticCurveTo(300 + i * 95, 450, 250 + i * 95, 640); g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

// ═════════ PLAN 1 : circuits + laser ═════════
function buildS1() {
  const sc = new THREE.Scene();
  sc.background = new THREE.Color("#02040a");
  sc.fog = new THREE.FogExp2("#02050d", 0.05);
  sc.environment = envTex; sc.environmentIntensity = 0.25;
  sc.add(new THREE.AmbientLight("#4a6cff", 0.25));
  const dl = new THREE.DirectionalLight("#9cc4ff", 1.6); dl.position.set(-4, 3, 5); sc.add(dl);
  const r = rng(11);
  const mats = [];
  for (let i = 0; i < 4; i++) {
    const [m, e] = circuitTextures(100 + i);
    mats.push(new THREE.MeshStandardMaterial({ map: m, emissiveMap: e, emissive: new THREE.Color("#ffffff"), emissiveIntensity: 1.3, metalness: 0.6, roughness: 0.4 }));
  }
  const side = new THREE.MeshStandardMaterial({ color: "#0a1224", metalness: 0.8, roughness: 0.35 });
  // mur de cartes électroniques
  for (let i = 0; i < 150; i++) {
    const w = 0.6 + r() * 2.6, h = 0.6 + r() * 2.2, d = 0.06 + r() * 0.35;
    const g = new THREE.BoxGeometry(w, h, d);
    const uv = g.attributes.uv; const su = w / 4, sv = h / 4, ou = r(), ov = r();
    for (let k = 0; k < uv.count; k++) uv.setXY(k, ou + uv.getX(k) * su, ov + uv.getY(k) * sv);
    const mat = mats[i % 4];
    mat.map.wrapS = mat.map.wrapT = mat.emissiveMap.wrapS = mat.emissiveMap.wrapT = THREE.RepeatWrapping;
    const m = new THREE.Mesh(g, [side, side, side, side, mat, side]);
    m.position.set((r() - .5) * 18, (r() - .5) * 11, -3 - r() * 9);
    m.rotation.set((r() - .5) * .25, (r() - .5) * .25, (r() - .5) * .1);
    sc.add(m);
  }
  // puce héroïne
  const hero = new THREE.Group();
  const [hm, he] = circuitTextures(7);
  const board = new THREE.Mesh(new THREE.BoxGeometry(1.5, 2.1, 0.08), [side, side, side, side,
    new THREE.MeshStandardMaterial({ map: hm, emissiveMap: he, emissive: new THREE.Color("#fff"), emissiveIntensity: 1.4, metalness: .5, roughness: .35 }), side]);
  hero.add(board);
  const chip = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.62, 0.12), new THREE.MeshStandardMaterial({ color: "#0b0d12", metalness: .9, roughness: .18 }));
  chip.position.z = 0.09; hero.add(chip);
  const pinM = new THREE.MeshStandardMaterial({ color: "#c9d2dd", metalness: 1, roughness: .25 });
  for (let s = 0; s < 4; s++) for (let k = 0; k < 10; k++) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.09, 0.02), pinM);
    const o = -0.27 + k * 0.06;
    if (s < 2) { p.position.set(o, s ? 0.36 : -0.36, 0.06); } else { p.rotation.z = Math.PI / 2; p.position.set(s === 2 ? 0.36 : -0.36, o, 0.06); }
    hero.add(p);
  }
  hero.position.set(0.9, -0.2, 1.2);
  sc.add(hero);
  // laser
  const laser = new THREE.Group();
  const core = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 1, 12, 1, true), new THREE.MeshBasicMaterial({ color: hot("#ffb060", 9), toneMapped: false }));
  const glow = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1, 16, 1, true), new THREE.MeshBasicMaterial({ color: hot("#ff6a10", 2.2), transparent: true, opacity: .35, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  core.position.y = glow.position.y = 0.5; laser.add(core, glow);
  sc.add(laser);
  const hitLight = new THREE.PointLight("#ff8a2a", 0, 8, 1.5); sc.add(hitLight);
  const hitBall = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 16), new THREE.MeshBasicMaterial({ color: hot("#ffd2a0", 6), toneMapped: false }));
  sc.add(hitBall);
  // étincelles
  const NS = 260, sp = new Float32Array(NS * 3), sv = [];
  for (let i = 0; i < NS; i++) sv.push([(r() - .5) * 3, r() * 2.5, (r() * .8 + .3) * 2.5, r()]);
  const sg = new THREE.BufferGeometry(); sg.setAttribute("position", new THREE.BufferAttribute(sp, 3));
  const sparks = new THREE.Points(sg, new THREE.PointsMaterial({ color: hot("#ffb46a", 3), size: 0.03, toneMapped: false, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  sc.add(sparks);
  // poussière
  const ND = 500, dp = new Float32Array(ND * 3);
  for (let i = 0; i < ND; i++) { dp[i * 3] = (r() - .5) * 14; dp[i * 3 + 1] = (r() - .5) * 8; dp[i * 3 + 2] = -6 + r() * 11; }
  const dg = new THREE.BufferGeometry(); dg.setAttribute("position", new THREE.BufferAttribute(dp, 3));
  const dust = new THREE.Points(dg, new THREE.PointsMaterial({ color: "#7fb2ff", size: 0.025, transparent: true, opacity: .7, depthWrite: false }));
  sc.add(dust);

  const src = new THREE.Vector3(9, 8, -6);
  return [sc, (t) => {
    const lt = t - S.s1[0];
    camera.fov = 40; camera.position.set(mix(-0.2, 0.5, lt / 3.6), mix(0.35, -0.1, lt / 3.6), mix(6.4, 4.4, eOut(lt / 3.6)));
    camera.lookAt(0.6, -0.15, 0.6); camera.rotation.z += mix(0.05, -0.03, lt / 3.6);
    hero.rotation.set(-0.35 + Math.sin(lt * .6) * .1, 0.45 + lt * .12, 0.5 + lt * 0.05);
    hero.position.y = -0.2 + Math.sin(lt * 1.3) * 0.05;
    dust.position.y = lt * 0.05;
    // laser : balaie et touche la puce à 1.3 s
    const hit = hero.localToWorld(new THREE.Vector3(0, 0, 0.16));
    const grow = eOut(lin(lt, 0.9, 1.3));
    const dir = hit.clone().sub(src); const len = dir.length();
    laser.visible = grow > 0;
    laser.position.copy(src);
    laser.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    laser.scale.set(1 + 0.3 * Math.sin(lt * 40), len * grow, 1 + 0.3 * Math.sin(lt * 40));
    const on = lt >= 1.3 ? 1 : 0;
    hitBall.visible = on > 0; hitBall.position.copy(hit); hitBall.scale.setScalar(1 + 0.4 * Math.sin(lt * 50));
    hitLight.position.copy(hit).add(new THREE.Vector3(0, 0, .3)); hitLight.intensity = on * (5 + 2 * Math.sin(lt * 37));
    const st = lt - 1.3;
    sparks.visible = st > 0;
    for (let i = 0; i < NS; i++) {
      const v = sv[i]; const age = ((st + v[3] * 1.2) % 1.2);
      sp[i * 3] = hit.x + v[0] * age; sp[i * 3 + 1] = hit.y + v[1] * age - 3.5 * age * age; sp[i * 3 + 2] = hit.z + v[2] * age;
    }
    sg.attributes.position.needsUpdate = true;
    bokeh.uniforms.focus.value = camera.position.distanceTo(hero.position);
    bokeh.uniforms.aperture.value = 0.0035; bokeh.uniforms.maxblur.value = 0.008;
    bloom.strength = 0.75; bloom.radius = 0.45; bloom.threshold = 0.9;
    finalPass.uniforms.uVig.value = 0.75;
  }];
}

// ═════════ PLAN 2 : planète qui éclate dans le désert ═════════
function noise3(x, y, z) {
  return Math.sin(x * 1.7 + Math.sin(y * 2.3)) * 0.5 + Math.sin(y * 2.9 + Math.sin(z * 1.9)) * 0.3 + Math.sin(z * 3.7 + x * 1.3) * 0.2;
}
function buildS2() {
  const sc = new THREE.Scene();
  sc.fog = new THREE.Fog("#a9a6c9", 25, 160);
  sc.environment = envTex; sc.environmentIntensity = 0.3;
  const sky = new THREE.Mesh(new THREE.SphereGeometry(200, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: {},
    vertexShader: `varying vec3 p; void main(){ p = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `varying vec3 p; void main(){ float h = clamp(p.y*2.2, 0.0, 1.0);
      vec3 top = vec3(0.26,0.31,0.54); vec3 hor = vec3(0.80,0.72,0.80);
      float sun = pow(max(dot(normalize(p), normalize(vec3(0.0,0.12,-1.0))),0.0), 60.0);
      gl_FragColor = vec4(mix(hor, top, pow(h,0.7)) + vec3(1.0,0.85,0.7)*sun*0.8, 1.0); }`
  }));
  sc.add(sky);
  sc.add(new THREE.HemisphereLight("#cdd6ff", "#6e6890", 0.8));
  const sun = new THREE.DirectionalLight("#fff0e0", 2.2); sun.position.set(0, 6, -30); sc.add(sun);
  const front = new THREE.DirectionalLight("#b9c6ff", 0.8); front.position.set(3, 4, 10); sc.add(front);
  // dunes
  const gg = new THREE.PlaneGeometry(260, 260, 200, 200); gg.rotateX(-Math.PI / 2);
  const pa = gg.attributes.position;
  for (let i = 0; i < pa.count; i++) {
    const x = pa.getX(i), z = pa.getZ(i);
    pa.setY(i, Math.sin(x * 0.06 + z * 0.03) * 1.3 + Math.sin(x * 0.17 - z * 0.11) * 0.45 + Math.sin(z * 0.05) * 1.5 + Math.max(0, -z - 60) * 0.12);
  }
  gg.computeVertexNormals();
  sc.add(new THREE.Mesh(gg, new THREE.MeshStandardMaterial({ color: "#8f97c2", roughness: 1 })));
  // silhouette de loup sur la dune
  const wc = document.createElement("canvas"); wc.width = 256; wc.height = 256; const w = wc.getContext("2d");
  w.fillStyle = "#1b1830"; w.beginPath();
  w.moveTo(60, 230); w.lineTo(70, 150); w.lineTo(95, 120); w.lineTo(150, 118); w.lineTo(170, 90); w.lineTo(160, 40);
  w.lineTo(178, 62); w.lineTo(190, 38); w.lineTo(196, 70); w.lineTo(226, 92); w.lineTo(214, 104); w.lineTo(186, 104);
  w.lineTo(182, 140); w.lineTo(178, 230); w.lineTo(166, 230); w.lineTo(165, 150); w.lineTo(110, 152); w.lineTo(100, 230);
  w.lineTo(88, 230); w.lineTo(86, 160); w.lineTo(72, 232); w.closePath(); w.fill();
  w.beginPath(); w.moveTo(70, 150); w.quadraticCurveTo(30, 170, 26, 215); w.lineTo(40, 205); w.quadraticCurveTo(50, 175, 74, 165); w.fill();
  const wt = new THREE.CanvasTexture(wc); wt.colorSpace = THREE.SRGBColorSpace;
  const wolf = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.6), new THREE.MeshBasicMaterial({ map: wt, transparent: true, fog: true }));
  wolf.position.set(2.6, 0.1, -10);
  sc.add(wolf);
  // planète en morceaux
  const R = 3.6, center = new THREE.Vector3(0, 7.2, -24);
  const r = rng(5);
  const seeds = []; for (let i = 0; i < 54; i++) { const v = new THREE.Vector3(r() - .5, r() - .5, r() - .5).normalize(); seeds.push(v); }
  const base = new THREE.IcosahedronGeometry(1, 5).toNonIndexed();
  const bp = base.attributes.position;
  const buckets = seeds.map(() => []);
  const disp = (v) => { const n = noise3(v.x * 3, v.y * 3, v.z * 3) * 0.05 + noise3(v.x * 9, v.y * 9, v.z * 9) * 0.02; return R * (1 + n); };
  for (let f = 0; f < bp.count; f += 3) {
    const cen = new THREE.Vector3();
    const vs = [0, 1, 2].map((k) => new THREE.Vector3().fromBufferAttribute(bp, f + k));
    vs.forEach((v) => cen.add(v)); cen.normalize();
    let best = 0, bd = -2; seeds.forEach((s, i) => { const d = s.dot(cen); if (d > bd) { bd = d; best = i; } });
    vs.forEach((v) => buckets[best].push(v.clone().multiplyScalar(disp(v))));
  }
  const rockM = new THREE.MeshStandardMaterial({ color: "#7d84a6", roughness: 0.75, metalness: 0.2, flatShading: true });
  const lavaM = new THREE.MeshBasicMaterial({ color: hot("#ff6a1a", 2.2), side: THREE.BackSide, toneMapped: false });
  const chunks = buckets.map((pts, i) => {
    const c = new THREE.Vector3(); pts.forEach((p) => c.add(p)); c.divideScalar(pts.length);
    const arr = new Float32Array(pts.length * 3); pts.forEach((p, k) => { arr[k * 3] = p.x - c.x; arr[k * 3 + 1] = p.y - c.y; arr[k * 3 + 2] = p.z - c.z; });
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(arr, 3)); g.computeVertexNormals();
    const grp = new THREE.Group();
    grp.add(new THREE.Mesh(g, rockM), new THREE.Mesh(g, lavaM));
    grp.userData = { c, dir: c.clone().normalize(), sp: 2.5 + r() * 6, rot: new THREE.Vector3(r() - .5, r() - .5, r() - .5).multiplyScalar(2.5), side: seeds[i].x };
    return grp;
  });
  const planet = new THREE.Group(); chunks.forEach((c) => planet.add(c)); planet.position.copy(center);
  const core = new THREE.Mesh(new THREE.SphereGeometry(R * 0.955, 48, 32), new THREE.MeshBasicMaterial({ color: hot("#ff7a20", 3), toneMapped: false }));
  planet.add(core);
  sc.add(planet);
  const flashLight = new THREE.PointLight("#ff9a4a", 0, 120, 1); flashLight.position.copy(center); sc.add(flashLight);
  // débris
  const debris = [];
  const dg = new THREE.TetrahedronGeometry(0.18, 0);
  for (let i = 0; i < 160; i++) {
    const m = new THREE.Mesh(dg, i % 3 ? rockM : new THREE.MeshBasicMaterial({ color: hot("#ff8a3a", 2), toneMapped: false }));
    m.userData = { dir: new THREE.Vector3(r() - .5, r() - .3, r() - .5).normalize(), sp: 3 + r() * 10, s: 0.4 + r() * 1.4, rot: r() * 6 };
    planet.add(m); debris.push(m);
  }
  const TE = 5.55;
  return [sc, (t) => {
    const lt = t - S.s2[0];
    camera.fov = 34;
    camera.position.set(mix(-0.4, 0.4, lt / 4), mix(1.6, 2.1, lt / 4), mix(6, 3.8, sm(lt / 4)));
    camera.lookAt(0, mix(4.2, 5.0, lt / 4), -24);
    planet.rotation.y = lt * 0.08;
    const pre = lin(t, 4.4, TE), dt = Math.max(0, t - TE);
    chunks.forEach((c) => {
      const u = c.userData;
      const tremble = pre * 0.03 * Math.sin(t * 60 + u.sp * 10);
      const out = dt > 0 ? u.sp * (1 - Math.exp(-dt * 1.4)) * 1.3 + dt * 0.4 : 0;
      c.position.copy(u.c).addScaledVector(u.dir, pre * 0.06 + tremble + out);
      c.rotation.set(u.rot.x * dt * .4, u.rot.y * dt * .4, u.rot.z * dt * .4);
      c.scale.setScalar(1 - pre * 0.03);
    });
    core.scale.setScalar(dt > 0 ? mix(1, 0.55, 1 - Math.exp(-dt * 2)) : 1);
    core.material.color.copy(hot("#ff7a20", 1.6 + pre * 2 + (dt > 0 ? 4 * Math.exp(-dt * 3) : 0)));
    debris.forEach((m) => {
      const u = m.userData; m.visible = dt > 0;
      m.position.copy(u.dir).multiplyScalar(3.1 + u.sp * (1 - Math.exp(-dt * 1.2)) * 1.4);
      m.scale.setScalar(u.s); m.rotation.set(u.rot + dt * 2, u.rot * 2 + dt, 0);
    });
    flashLight.intensity = dt > 0 ? 250 * Math.exp(-dt * 2.5) : pre * 60;
    bokeh.uniforms.focus.value = camera.position.distanceTo(center); bokeh.uniforms.aperture.value = 0.0004; bokeh.uniforms.maxblur.value = 0.005;
    bloom.strength = 0.6 + (dt > 0 ? 0.6 * Math.exp(-dt * 2) : 0); bloom.radius = 0.5; bloom.threshold = 1.0;
    finalPass.uniforms.uVig.value = 0.35;
  }];
}

// ═════════ PLAN 3 : duel VS ═════════
function buildS3() {
  const sc = new THREE.Scene();
  sc.background = new THREE.Color("#04050a");
  sc.fog = new THREE.Fog("#04050a", 8, 30);
  sc.environment = envTex; sc.environmentIntensity = 0.5;
  sc.add(new THREE.AmbientLight("#ffffff", 0.08));
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ color: "#07080d", metalness: 1, roughness: 0.28 }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -2.2; sc.add(floor);
  const redL = new THREE.PointLight("#ff3b1a", 14, 20, 1.6); const blueL = new THREE.PointLight("#2fb4ff", 14, 20, 1.6);
  sc.add(redL, blueL);
  const top = new THREE.SpotLight("#ffffff", 40, 30, 0.5, 0.6, 1.5); top.position.set(0, 9, 3); sc.add(top); sc.add(top.target);
  function slab(color, name, num) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(2.3, 3.3, 0.22), new THREE.MeshPhysicalMaterial({ color, roughness: 0.18, metalness: 0.2, clearcoat: 1, clearcoatRoughness: 0.1, emissive: color, emissiveIntensity: 0.12 }));
    const lab = new THREE.Mesh(new THREE.PlaneGeometry(2.3 * 0.97, 3.3 * 0.97), new THREE.MeshBasicMaterial({ map: slabLabel(name, num, color), transparent: true }));
    lab.position.z = 0.115;
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(body.geometry), new THREE.LineBasicMaterial({ color: hot(color, 2.5), toneMapped: false }));
    g.add(body, lab, edges);
    sc.add(g);
    return g;
  }
  const A = slab("#e3350d", "LION", "N° 001"), B = slab("#30a7d7", "TIGRE", "N° 002");
  // éclats
  const r = rng(21);
  const shards = [];
  const shardG = [];
  for (let i = 0; i < 5; i++) {
    const g = new THREE.BufferGeometry();
    const p = [0, 0, 0, (r() - .5) * .8, (r() - .5) * .8, 0, (r() - .5) * .8, (r() - .5) * .8, 0];
    g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3)); g.computeVertexNormals(); shardG.push(g);
  }
  const shM = [new THREE.MeshPhysicalMaterial({ color: "#e3350d", emissive: "#e3350d", emissiveIntensity: 0.6, roughness: .1, metalness: .3, side: THREE.DoubleSide }),
    new THREE.MeshPhysicalMaterial({ color: "#30a7d7", emissive: "#30a7d7", emissiveIntensity: 0.6, roughness: .1, metalness: .3, side: THREE.DoubleSide }),
    new THREE.MeshBasicMaterial({ color: hot("#ffcb05", 2.5), side: THREE.DoubleSide, toneMapped: false })];
  for (let i = 0; i < 260; i++) {
    const m = new THREE.Mesh(shardG[i % 5], shM[i % 9 === 0 ? 2 : i % 2]);
    const th = r() * Math.PI * 2, ph = (r() - .5) * 1.6;
    m.userData = { dir: new THREE.Vector3(Math.cos(th) * Math.cos(ph), Math.sin(ph) + .15, Math.sin(th) * Math.cos(ph) * .6 + .4).normalize(), sp: 3 + r() * 9, rot: new THREE.Vector3(r(), r(), r()).multiplyScalar(8), s: .4 + r() * 1.3 };
    sc.add(m); shards.push(m);
  }
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.9, 1, 96), new THREE.MeshBasicMaterial({ color: hot("#ffcb05", 2.5), transparent: true, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  sc.add(ring);
  const flash = new THREE.PointLight("#ffe29a", 0, 40, 1.2); sc.add(flash);
  const TI = 9.55;
  return [sc, (t) => {
    const lt = t - S.s3[0];
    const ang = mix(-0.35, 0.3, sm(lin(lt, 0, 4)));
    const rad = mix(10.5, 8.2, eOut(lin(lt, 0, 4)));
    camera.fov = 38;
    const shake = t > TI ? 0.12 * Math.exp(-(t - TI) * 5) : 0;
    camera.position.set(Math.sin(ang) * rad + Math.sin(t * 90) * shake, 0.6 + Math.cos(t * 77) * shake, Math.cos(ang) * rad);
    camera.lookAt(0, 0.1, 0);
    const rush = eIn(lin(t, 8.95, TI));
    const sep = mix(3.1, 1.15, rush);
    A.position.set(-sep, 0.15 + Math.sin(lt * 1.7) * 0.08 * (1 - rush), 0); A.rotation.set(0, mix(0.42, 0.05, rush), mix(0.04, -0.08, rush));
    B.position.set(sep, 0.15 + Math.sin(lt * 1.7 + 1.5) * 0.08 * (1 - rush), 0); B.rotation.set(0, mix(-0.42, -0.05, rush), mix(-0.04, 0.08, rush));
    const hit = t >= TI; A.visible = B.visible = !hit;
    redL.position.set(-3.5, 1.5, 2.5); blueL.position.set(3.5, 1.5, 2.5);
    const dt = Math.max(0, t - TI);
    shards.forEach((m) => {
      const u = m.userData; m.visible = hit;
      const d = u.sp * (1 - Math.exp(-dt * 1.6)) * 1.2 + dt * 0.3;
      m.position.copy(u.dir).multiplyScalar(d).add(new THREE.Vector3(0, 0.15, 0));
      m.position.y -= dt * dt * 0.4;
      m.rotation.set(u.rot.x * (dt * .6 + .1), u.rot.y * (dt * .6 + .1), u.rot.z * (dt * .6));
      m.scale.setScalar(u.s);
    });
    ring.visible = hit; ring.position.set(0, 0.15, 0); ring.lookAt(camera.position);
    ring.scale.setScalar(0.3 + eOut(clamp(dt / 0.7)) * 6); ring.material.opacity = 1 - clamp(dt / 0.5);
    flash.position.set(0, 0.5, 1.5); flash.intensity = hit ? 120 * Math.exp(-dt * 3) : 0;
    bokeh.uniforms.focus.value = camera.position.length(); bokeh.uniforms.aperture.value = 0.0012; bokeh.uniforms.maxblur.value = 0.006;
    bloom.strength = 0.7 + (hit ? 0.6 * Math.exp(-dt * 3) : 0); bloom.radius = 0.45; bloom.threshold = 0.9;
    finalPass.uniforms.uVig.value = 0.7;
  }];
}

// ═════════ PLAN 4 : pluie de gélules ═════════
function buildS4() {
  const sc = new THREE.Scene();
  sc.background = new THREE.Color("#2b4a64");
  sc.fog = new THREE.Fog("#2b4a64", 10, 34);
  sc.environment = envTex; sc.environmentIntensity = 0.9;
  sc.add(new THREE.HemisphereLight("#e8f4ff", "#1c3048", 1.4));
  const key = new THREE.DirectionalLight("#ffffff", 2.2); key.position.set(4, 10, 6); sc.add(key);
  const cols = ["#fd7d24", "#4592c4", "#7b62a3", "#d8327a", "#51c4e7", "#4ea34e", "#f7de3f", "#e3350d"];
  const r = rng(33);
  const N = 70, inst = [];
  cols.forEach((c) => {
    const g = new THREE.CapsuleGeometry(0.26, 0.62, 10, 20);
    const pos = g.attributes.position, ca = new Float32Array(pos.count * 3);
    const cc = new THREE.Color(c), wh = new THREE.Color("#f4f6fa");
    for (let i = 0; i < pos.count; i++) { const k = pos.getY(i) > 0 ? cc : wh; ca[i * 3] = k.r; ca[i * 3 + 1] = k.g; ca[i * 3 + 2] = k.b; }
    g.setAttribute("color", new THREE.BufferAttribute(ca, 3));
    const m = new THREE.InstancedMesh(g, new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.28, clearcoat: 1, clearcoatRoughness: 0.08 }), N);
    const data = [];
    for (let i = 0; i < N; i++) data.push({ x: (r() - .5) * 20, z: -18 + r() * 22, y0: r() * 22, v: 1.4 + r() * 1.6, ax: new THREE.Vector3(r() - .5, r() - .5, r() - .5).normalize(), w: 0.6 + r() * 1.6, a0: r() * 6 });
    sc.add(m); inst.push([m, data]);
  });
  const dummy = new THREE.Object3D();
  return [sc, (t) => {
    const lt = t - S.s4[0];
    camera.fov = 42;
    camera.position.set(Math.sin(lt * .12) * 1.2, mix(1.6, 0.8, lt / 3.4), 8);
    camera.lookAt(0, mix(-0.5, -1.2, lt / 3.4), -2);
    camera.rotation.z += mix(-0.05, 0.05, lt / 3.4);
    inst.forEach(([m, data]) => {
      data.forEach((d, i) => {
        let y = d.y0 - (lt + 2) * d.v; y = ((y % 22) + 22) % 22 - 11;
        dummy.position.set(d.x, y, d.z);
        dummy.quaternion.setFromAxisAngle(d.ax, d.a0 + lt * d.w);
        dummy.updateMatrix(); m.setMatrixAt(i, dummy.matrix);
      });
      m.instanceMatrix.needsUpdate = true;
    });
    bokeh.uniforms.focus.value = 8.5; bokeh.uniforms.aperture.value = 0.006; bokeh.uniforms.maxblur.value = 0.012;
    bloom.strength = 0.25; bloom.radius = 0.4; bloom.threshold = 1.0;
    finalPass.uniforms.uVig.value = 0.5;
  }];
}

// ═════════ PLAN 5 : barres de stats ═════════
const STATS = [[85, 90], [60, 62], [65, 70]];
let barWorld = [];
function buildS5() {
  const sc = new THREE.Scene();
  sc.background = new THREE.Color("#05060b");
  sc.fog = new THREE.Fog("#05060b", 9, 26);
  sc.environment = envTex; sc.environmentIntensity = 0.3;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: "#090a10", metalness: 1, roughness: 0.22 }));
  floor.rotation.x = -Math.PI / 2; sc.add(floor);
  sc.add(new THREE.AmbientLight("#ffffff", 0.1));
  const bars = [];
  STATS.forEach((pair, i) => pair.forEach((v, j) => {
    const col = j ? "#30a7d7" : "#e3350d";
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1, 0.7), new THREE.MeshPhysicalMaterial({ color: col, emissive: col, emissiveIntensity: 0.3, roughness: .2, clearcoat: 1 }));
    m.geometry.translate(0, 0.5, 0);
    const cap = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.05, 0.72), new THREE.MeshBasicMaterial({ color: hot(col, 3), toneMapped: false }));
    m.userData = { v, x: (i - 1) * 2.9 + (j ? 0.45 : -0.45), delay: i * 0.18 + j * 0.08, cap };
    sc.add(m, cap); bars.push(m);
    const l = new THREE.PointLight(col, 3, 5, 1.5); l.position.set(m.userData.x, 1.5, 1); sc.add(l);
  }));
  return [sc, (t) => {
    const lt = t - S.s5[0];
    camera.fov = 36;
    camera.position.set(mix(-1.6, 1.2, sm(lt / 2.2)), mix(1.2, 2.2, lt / 2.2), mix(9.5, 8.4, lt / 2.2));
    camera.lookAt(0, 1.5, 0);
    barWorld = [];
    bars.forEach((m) => {
      const u = m.userData, k = eBack(lin(lt, 0.1 + u.delay, 0.9 + u.delay));
      const h = Math.max(0.001, (u.v / 100) * 3.6 * k);
      m.position.set(u.x, 0, 0); m.scale.y = h;
      u.cap.position.set(u.x, h, 0);
      barWorld.push({ top: new THREE.Vector3(u.x, h + 0.12, 0), base: new THREE.Vector3(u.x, 0, 0), k, v: u.v });
    });
    bokeh.uniforms.focus.value = camera.position.distanceTo(new THREE.Vector3(0, 1.5, 0)); bokeh.uniforms.aperture.value = 0.0012; bokeh.uniforms.maxblur.value = 0.006;
    bloom.strength = 0.7; bloom.radius = 0.45; bloom.threshold = 0.9;
    finalPass.uniforms.uVig.value = 0.7;
  }];
}

// ═════════ PLAN 6 : logo ═════════
function buildS6() {
  const sc = new THREE.Scene();
  sc.background = new THREE.Color("#03050d");
  const bg = new THREE.Mesh(new THREE.PlaneGeometry(60, 34), new THREE.ShaderMaterial({
    depthWrite: false, uniforms: { k: { value: 0 } },
    vertexShader: `varying vec2 v; void main(){ v = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `uniform float k; varying vec2 v; void main(){ float d = length((v-0.5)*vec2(1.7,1.0));
      vec3 c = mix(vec3(0.09,0.16,0.38), vec3(0.01,0.02,0.05), smoothstep(0.0,0.6,d));
      gl_FragColor = vec4(c*(0.4+0.6*k), 1.0); }`
  }));
  bg.position.z = -12; sc.add(bg);
  const r = rng(77), N = 5000;
  const from = new Float32Array(N * 3), to = new Float32Array(N * 3), cur = new Float32Array(N * 3), col = new Float32Array(N * 3);
  const pal = [new THREE.Color("#ffcb05"), new THREE.Color("#2a75bb"), new THREE.Color("#ffffff"), new THREE.Color("#ee6b2f")];
  for (let i = 0; i < N; i++) {
    const v = new THREE.Vector3(r() - .5, r() - .5, r() - .5).normalize().multiplyScalar(14 + r() * 10);
    from.set([v.x, v.y, v.z], i * 3);
    const a = r() * Math.PI * 2, rr = 5.2 + (r() - .5) * 0.5 * (1 + r() * 2);
    to.set([Math.cos(a) * rr * 1.55, Math.sin(a) * rr * 0.62, (r() - .5) * 1.2], i * 3);
    const c = pal[Math.floor(r() ** 1.5 * 4)]; col.set([c.r * 1.6, c.g * 1.6, c.b * 1.6], i * 3);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(cur, 3)); g.setAttribute("color", new THREE.BufferAttribute(col, 3));
  const pts = new THREE.Points(g, new THREE.PointsMaterial({ size: 0.035, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  sc.add(pts);
  return [sc, (t) => {
    const lt = t - S.s6[0];
    camera.fov = 40; camera.position.set(0, 0, mix(15, 13, lt / 2.8)); camera.lookAt(0, 0, 0);
    const k = eOut(lin(lt, 0, 0.9));
    for (let i = 0; i < N * 3; i++) cur[i] = mix(from[i], to[i], k);
    g.attributes.position.needsUpdate = true;
    pts.rotation.z = lt * 0.12; pts.scale.setScalar(1 + lt * 0.03);
    bg.material.uniforms.k.value = k;
    bokeh.uniforms.focus.value = 14; bokeh.uniforms.aperture.value = 0.001; bokeh.uniforms.maxblur.value = 0.004;
    bloom.strength = 0.8; bloom.radius = 0.45; bloom.threshold = 0.7;
    finalPass.uniforms.uVig.value = 0.6;
  }];
}

// ─── texte ───
const $ = (id) => document.getElementById(id);
function txt(id, t, a, b, o = {}) {
  const el = $(id);
  if (!el.dataset.ls) el.dataset.ls = getComputedStyle(el).letterSpacing;
  const inD = o.inD ?? 0.45, outD = o.outD ?? 0.35;
  const i = lin(t, a, a + inD), u = 1 - lin(t, b - outD, b);
  const v = Math.min(i, u);
  if (v <= 0) { el.style.opacity = 0; return 0; }
  const blur = (1 - eOut(v)) * (o.blur ?? 22);
  const ca = 2 + (1 - v) * 18 + (o.ca ?? 0);
  const sc = o.scale ? mix(o.scale, 1, eOut(i)) : 1;
  const sp = o.track != null ? mix(o.track, 0, eOut(i)) : 0;
  el.style.opacity = sm(v);
  el.style.filter = `blur(${blur.toFixed(2)}px)`;
  el.style.transform = `translateY(${((1 - eOut(i)) * (o.dy ?? 30)).toFixed(1)}px) scale(${sc.toFixed(4)})`;
  if (o.track != null) el.style.letterSpacing = `calc(${el.dataset.ls} + ${sp.toFixed(1)}px)`;
  if (!o.noCA) el.style.textShadow = `${-ca}px 0 rgba(255,30,70,.75), ${ca}px 0 rgba(0,210,255,.75)` + (o.glow ? `, 0 0 40px ${o.glow}` : "");
  return v;
}

// ─── orchestration ───
let shots;
function renderAt(t) {
  const key = Object.keys(S).find((k) => t >= S[k][0] && t < S[k][1]) || "s6";
  const sc = shots[key].scene; shots[key].update(t);
  renderPass.scene = sc; bokeh.scene = sc;
  camera.updateProjectionMatrix();
  // transitions : flou + aberration autour des coupes
  let spike = 0; CUTS.forEach((c) => { spike = Math.max(spike, Math.exp(-Math.pow((t - c) / 0.12, 2))); });
  bokeh.uniforms.maxblur.value += spike * 0.03; bokeh.uniforms.aperture.value += spike * 0.05;
  finalPass.uniforms.uCA.value = 0.004 + spike * 0.06 + (t > 5.55 && t < 6.3 ? 0.03 * Math.exp(-(t - 5.55) * 5) : 0) + (t > 9.55 && t < 10.3 ? 0.05 * Math.exp(-(t - 9.55) * 5) : 0);
  finalPass.uniforms.uFlash.value = Math.max(t > 5.55 ? 0.35 * Math.exp(-(t - 5.55) * 8) : 0, t > 9.55 ? 0.45 * Math.exp(-(t - 9.55) * 8) : 0, spike * 0.12);
  finalPass.uniforms.uFade.value = Math.max(1 - lin(t, 0, 0.5), lin(t, 19.45, 20));
  finalPass.uniforms.uTime.value = t;
  composer.render();

  // textes
  txt("t1a", t, 0.9, 3.4, { track: 40, blur: 26 });
  txt("t1b", t, 1.6, 3.4, { blur: 14, dy: 16 });
  txt("t2a", t, 4.3, 7.45, { track: 30 });
  txt("t2b", t, 5.6, 7.45, { scale: 1.5, blur: 30, glow: "rgba(255,120,40,.8)", inD: 0.3 });
  txt("vs", t, 9.55, 11.4, { scale: 2.4, blur: 30, inD: 0.28, dy: 0, glow: "rgba(255,203,5,.55)" });
  txt("t3b", t, 10.2, 11.45, { track: 20 });
  // compteur
  const cv = txt("count", t, 11.9, 14.85, { blur: 18, dy: 0 });
  if (cv > 0) $("count").textContent = String(Math.round(100 * eOut(lin(t, 12.0, 13.6)))).padStart(3, "0");
  txt("t4b", t, 12.5, 14.85, { track: 30 });
  txt("t4c", t, 13.0, 14.85, { blur: 10, dy: 14 });
  // stats
  txt("t5h", t, 15.15, 17.0, { blur: 10, dy: 10 });
  const sv = Math.min(lin(t, 15.2, 15.6), 1 - lin(t, 16.05, 16.3));
  STATS.forEach((p, i) => {
    const el = $("lab" + i);
    if (key === "s5" && barWorld.length) {
      const b = barWorld[i * 2].base.clone().add(barWorld[i * 2 + 1].base).multiplyScalar(0.5).project(camera);
      el.style.left = ((b.x + 1) / 2 * W) + "px"; el.style.top = ((1 - (b.y + 1) / 2) * H + 18) + "px";
      el.style.opacity = sv; el.style.filter = `blur(${(1 - sv) * 10}px)`;
    } else el.style.opacity = 0;
  });
  for (let i = 0; i < 6; i++) {
    const el = $("n" + i);
    if (key === "s5" && barWorld[i]) {
      const b = barWorld[i].top.clone().project(camera);
      el.style.left = ((b.x + 1) / 2 * W) + "px"; el.style.top = ((1 - (b.y + 1) / 2) * H) + "px";
      el.textContent = Math.round(barWorld[i].v * clamp(barWorld[i].k));
      el.style.color = i % 2 ? "#8fdcff" : "#ff9a80";
      el.style.opacity = Math.min(clamp(barWorld[i].k * 2), sv);
    } else el.style.opacity = 0;
  }
  txt("t5v", t, 16.3, 17.15, { scale: 1.6, blur: 26, inD: 0.25, outD: 0.2, dy: 0, glow: "rgba(48,167,215,.8)" });
  txt("t5w", t, 16.45, 17.15, { blur: 12, outD: 0.2, dy: 12 });
  // logo
  txt("logo", t, 17.75, 20.1, { scale: 1.35, blur: 30, inD: 0.4, dy: 0, noCA: true });
  txt("tag", t, 18.35, 20.1, { track: 20, blur: 14, dy: 14 });
  txt("cta", t, 18.8, 20.1, { blur: 10, dy: 24, noCA: true });
  $("logo").style.transform += " rotate(-4deg)";
}

async function init() {
  await Promise.all(["120px Anton", "100px 'Lilita One'", "700 40px 'Exo 2'", "600 40px 'Exo 2'"].map((f) => document.fonts.load(f)));
  shots = {};
  for (const [k, fn] of [["s1", buildS1], ["s2", buildS2], ["s3", buildS3], ["s4", buildS4], ["s5", buildS5], ["s6", buildS6]]) {
    const [scene, update] = fn();
    shots[k] = { update, scene };
  }
  window.renderAt = renderAt;
  window.ready = true;
}
init();
