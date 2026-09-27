(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const byId = (id) => ANIMALS.find((a) => a.id === +id);
  const byName = (n) => ANIMALS.find((a) => a.nom === n);
  const num = (id) => "N° " + String(id).padStart(3, "0");
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  /* ─────────────── Photos (Wikipédia) ─────────────── */
  const IMG_KEY = "duel-sauvage-img-v1";
  let imgs = {};
  try { imgs = JSON.parse(localStorage.getItem(IMG_KEY)) || {}; } catch (e) { imgs = {}; }

  function pic(a, cls = "") {
    return `<div class="pic ${cls}" data-aid="${a.id}"><span class="pic-emoji">${a.emoji}</span>${imgTag(a)}</div>`;
  }
  function imgTag(a) {
    const src = imgs[a.wiki];
    return src ? `<img src="${esc(src)}" alt="${esc(a.nom)}" loading="lazy" onerror="this.remove()">` : "";
  }
  function paintImages() {
    $$(".pic[data-aid]").forEach((el) => {
      if (el.querySelector("img")) return;
      const a = byId(el.dataset.aid);
      if (a && imgs[a.wiki]) el.insertAdjacentHTML("beforeend", imgTag(a));
    });
  }
  async function loadImages() {
    const missing = [...new Set(ANIMALS.map((a) => a.wiki))].filter((t) => !(t in imgs));
    for (let i = 0; i < missing.length; i += 50) {
      const batch = missing.slice(i, i + 50);
      const url = "https://en.wikipedia.org/w/api.php?action=query&format=json&origin=*&redirects=1" +
        "&prop=pageimages&piprop=thumbnail&pithumbsize=640&titles=" + encodeURIComponent(batch.join("|"));
      try {
        const res = await fetch(url);
        const q = (await res.json()).query || {};
        const map = {};
        (q.normalized || []).forEach((n) => (map[n.from] = n.to));
        const redir = {};
        (q.redirects || []).forEach((r) => (redir[r.from] = r.to));
        const found = {};
        Object.values(q.pages || {}).forEach((p) => { if (p.thumbnail) found[p.title] = p.thumbnail.source; });
        batch.forEach((t) => {
          let k = map[t] || t;
          k = redir[k] || k;
          imgs[t] = found[k] || null;
        });
      } catch (e) { /* hors ligne : on garde les emojis */ }
    }
    try { localStorage.setItem(IMG_KEY, JSON.stringify(imgs)); } catch (e) { /* stockage indisponible */ }
    paintImages();
  }

  /* ─────────────── Petits composants ─────────────── */
  const badge = (h) => {
    const c = HABITATS[h] || { color: "#a4acaf", text: "#fff" };
    return `<span class="badge" style="background:${c.color};color:${c.text}">${h}</span>`;
  };
  const badges = (a) => a.habitats.map(badge).join("") +
    (a.venin ? `<span class="badge badge-venin">${a.electrique ? "Électrique" : "Venimeux"}</span>` : "");

  /* ─────────────── Carrousel « à l'affiche » ─────────────── */
  function renderCarousel() {
    const pool = [...ANIMALS].sort(() => Math.random() - 0.5).slice(0, 12);
    const track = $("#carTrack");
    track.innerHTML = pool.map((a, i) => `
      <article class="feat${i === 2 ? " active" : ""}" data-open="${a.id}" tabindex="0">
        <div class="feat-img">
          <span class="feat-num">${a.id}</span>
          ${pic(a)}
        </div>
        <div class="feat-info">
          <div class="feat-name"><span>${esc(a.nom)}</span><span class="feat-id">${a.id}</span></div>
          <div class="feat-more">
            <div class="feat-row"><span>Type</span><span>${a.habitats.map(badge).join("")}</span></div>
            <div class="feat-row"><span>Talent</span><span>${esc(a.talent)}</span></div>
          </div>
        </div>
      </article>`).join("");
    $$(".feat", track).forEach((el) => {
      el.addEventListener("mouseenter", () => setActive(el));
      el.addEventListener("focus", () => setActive(el));
    });
    function setActive(el) { $$(".feat", track).forEach((x) => x.classList.toggle("active", x === el)); }
    $("#carPrev").onclick = () => track.scrollBy({ left: -track.clientWidth * 0.7, behavior: "smooth" });
    $("#carNext").onclick = () => track.scrollBy({ left: track.clientWidth * 0.7, behavior: "smooth" });
  }

  /* ─────────────── Arène ─────────────── */
  const state = { A: byName("Lion").id, B: byName("Tigre du Bengale").id, terrain: "auto" };

  function renderSlot(slot) {
    const el = $("#slot" + slot);
    const a = byId(state[slot]);
    const side = slot === "A" ? "Coin rouge" : "Coin bleu";
    if (!a) {
      el.innerHTML = `<span class="corner-side">${side}</span><div class="corner-empty">?</div><div class="corner-name">Choisir un combattant</div>`;
      return;
    }
    el.innerHTML = `
      <span class="corner-side">${side}</span>
      ${pic(a, "corner-pic")}
      <div class="corner-body">
        <div class="corner-name">${esc(a.nom)} <small>${num(a.id)}</small></div>
        <div class="badges">${badges(a)}</div>
        <div class="corner-mini">
          <span><b>${Engine.fmtKg(a.kg)}</b>poids</span>
          <span><b>${a.kmh} km/h</b>vitesse</span>
          <span><b>${a.att}</b>attaque</span>
        </div>
        <span class="corner-change">Changer ↻</span>
      </div>`;
  }
  function renderSlots() { renderSlot("A"); renderSlot("B"); }

  function setTerrain(t) {
    state.terrain = t;
    $$("#terrainPick button").forEach((b) => b.classList.toggle("on", b.dataset.t === t));
  }

  function fight(scroll = true) {
    const a = byId(state.A), b = byId(state.B);
    if (!a || !b) return;
    const r = Engine.duel(a, b, state.terrain);
    renderResult(r);
    try { history.replaceState(null, "", `?a=${a.id}&b=${b.id}&t=${state.terrain}#arene`); } catch (e) { /* ignore */ }
    if (scroll) $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function statRows(a, b) {
    const logKg = (kg) => Math.log10(kg) + 4;
    const rows = [
      ["Poids", Engine.fmtKg(a.kg), Engine.fmtKg(b.kg), logKg(a.kg), logKg(b.kg), 9.3],
      ["Taille", a.taille.toLocaleString("fr-FR") + " m", b.taille.toLocaleString("fr-FR") + " m", Math.log10(a.taille * 100 + 1), Math.log10(b.taille * 100 + 1), 3.5],
      ["Vitesse", a.kmh + " km/h", b.kmh + " km/h", Engine.speedScore(a.kmh), Engine.speedScore(b.kmh), 100],
      ["Attaque", a.att, b.att, a.att, b.att, 100],
      ["Défense", a.def, b.def, a.def, b.def, 100],
      ["Agilité", a.agi, b.agi, a.agi, b.agi, 100],
      ["Endurance", a.end, b.end, a.end, b.end, 100],
      ["Intelligence", a.int, b.int, a.int, b.int, 100],
      ["Venin", a.venin + "/3", b.venin + "/3", a.venin, b.venin, 3],
      ["Armure", a.armure + "/3", b.armure + "/3", a.armure, b.armure, 3]
    ];
    return rows.map(([label, va, vb, na, nb, max]) => `
      <div class="cmp-row">
        <span class="cmp-val ${na > nb ? "win" : ""}">${va}</span>
        <div class="cmp-bar left"><i style="width:${na / max * 100}%"></i></div>
        <span class="cmp-label">${label}</span>
        <div class="cmp-bar right"><i style="width:${nb / max * 100}%"></i></div>
        <span class="cmp-val ${nb > na ? "win" : ""}">${vb}</span>
      </div>`).join("");
  }

  function factorRows(r) {
    const max = Math.max(...r.factors.map((f) => Math.abs(f.val)), 1);
    return r.factors.map((f) => {
      const w = Math.abs(f.val) / max * 50;
      const who = f.val > 0 ? r.a : r.b;
      return `
      <div class="fac">
        <div class="fac-head"><b>${f.label}</b><span class="fac-pts ${f.val > 0 ? "red" : "blue"}">+${Math.abs(f.val).toFixed(1)} pts pour ${esc(who.nom)}</span></div>
        <div class="fac-bar"><i class="${f.val > 0 ? "red" : "blue"}" style="width:${w}%;${f.val > 0 ? "right:50%" : "left:50%"}"></i></div>
        <p>${esc(f.desc)}</p>
      </div>`;
    }).join("");
  }

  function renderResult(r) {
    const pA = Math.round(r.pA * 100), pB = 100 - pA;
    const draw = r.a.id === r.b.id;
    const wins = Math.round(r.pW * 10);
    const T = Engine.TERRAINS[r.terrain];
    const box = $("#result");
    box.hidden = false;
    box.innerHTML = `
      <div class="res-banner ${draw ? "" : r.winner === r.a ? "red" : "blue"}">
        ${pic(r.winner, "res-pic")}
        <div class="res-text">
          <span class="res-kicker">${draw ? "Match nul" : "Vainqueur probable"} · ${T.emoji} ${T.nom}${r.auto ? " (auto)" : ""}</span>
          <h2>${esc(r.winner.nom)}</h2>
          <p>${esc(r.verdict)}</p>
          <div class="pips" title="Sur 10 duels">${Array.from({ length: 10 }, (_, i) => `<span class="${i < wins ? "on" : ""}"></span>`).join("")}<em>${draw ? 5 : wins} victoire${wins > 1 ? "s" : ""} sur 10</em></div>
        </div>
      </div>

      <div class="prob">
        <div class="prob-names"><span>${esc(r.a.nom)}</span><span>${esc(r.b.nom)}</span></div>
        <div class="prob-bar"><i class="red" style="width:${pA}%">${pA} %</i><i class="blue" style="width:${pB}%">${pB} %</i></div>
      </div>

      <div class="res-cols">
        <div class="res-card">
          <h3>Face-à-face des stats</h3>
          <div class="cmp-head"><span class="red">${esc(r.a.nom)}</span><span class="blue">${esc(r.b.nom)}</span></div>
          ${statRows(r.a, r.b)}
        </div>
        <div class="res-card">
          <h3>Facteurs décisifs</h3>
          <div class="cmp-head"><span class="red">← avantage ${esc(r.a.nom)}</span><span class="blue">avantage ${esc(r.b.nom)} →</span></div>
          ${factorRows(r)}
        </div>
      </div>

      <div class="res-card story">
        <h3>Déroulé du combat</h3>
        <ol class="phases">${r.story.map((p) => `<li><h4>${esc(p.t)}</h4><p>${esc(p.x)}</p></li>`).join("")}</ol>
      </div>

      <div class="res-actions">
        <span>Rejouer sur un autre terrain :</span>
        ${["terre", "eau", "air"].map((t) => `<button class="btn-ghost dark" data-replay="${t}">${Engine.TERRAINS[t].emoji} ${Engine.TERRAINS[t].nom}</button>`).join("")}
      </div>`;
    $$("[data-replay]", box).forEach((btn) => btn.onclick = () => { setTerrain(btn.dataset.replay); fight(false); });
  }

  /* ─────────────── Duels légendaires ─────────────── */
  const LEGENDS = [
    ["Lion", "Tigre du Bengale", "Le roi de la savane contre le seigneur de la jungle"],
    ["Orque", "Grand requin blanc", "Le choc des super-prédateurs marins"],
    ["Mangouste grise", "Cobra royal", "Réflexes contre venin"],
    ["Hippopotame", "Crocodile du Nil", "La guerre des rivières africaines"],
    ["Gorille", "Ours brun", "Force brute contre force brute"],
    ["Ours polaire", "Morse", "Duel sur la banquise"],
    ["Cachalot", "Calmar géant", "Le combat des abysses"],
    ["Ratel", "Lion", "Le plus téméraire des mammifères"],
    ["Jaguar", "Anaconda vert", "Les maîtres de l'Amazonie"],
    ["Éléphant d'Afrique", "Rhinocéros blanc", "Le choc des titans"],
    ["Crocodile marin", "Grand requin blanc", "Le face-à-face côtier"],
    ["Aigle royal", "Renard roux", "L'attaque venue du ciel"]
  ];
  function renderLegends() {
    $("#legendGrid").innerHTML = LEGENDS.map(([x, y, sub], i) => {
      const a = byName(x), b = byName(y);
      return `<button class="legend c${i % 4}" data-a="${a.id}" data-b="${b.id}">
        <div class="legend-pics">${pic(a)}${pic(b)}<span class="legend-vs">VS</span></div>
        <div class="legend-txt"><b>${esc(a.nom)} vs ${esc(b.nom)}</b><span>${esc(sub)}</span></div>
      </button>`;
    }).join("");
    $$(".legend").forEach((el) => el.onclick = () => {
      state.A = +el.dataset.a; state.B = +el.dataset.b;
      setTerrain("auto"); renderSlots(); paintImages(); fight();
    });
  }

  /* ─────────────── Animalédex ─────────────── */
  function filterList(q, classe, habitat) {
    const nq = norm(q.trim());
    return ANIMALS.filter((a) =>
      (!nq || norm(a.nom).includes(nq) || norm(a.sci).includes(nq) || String(a.id).padStart(3, "0").includes(nq)) &&
      (!classe || a.classe === classe) &&
      (!habitat || a.habitats.includes(habitat)));
  }
  function renderDex() {
    const list = filterList($("#dexSearch").value, $("#fClasse").value, $("#fHabitat").value);
    const s = $("#fSort").value;
    const sorters = {
      id: (x, y) => x.id - y.id,
      nom: (x, y) => x.nom.localeCompare(y.nom, "fr"),
      kg: (x, y) => y.kg - x.kg,
      kmh: (x, y) => y.kmh - x.kmh,
      att: (x, y) => y.att - x.att,
      venin: (x, y) => y.venin - x.venin || x.id - y.id
    };
    list.sort(sorters[s]);
    $("#dexCount").textContent = list.length + (list.length > 1 ? " animaux" : " animal");
    $("#dexGrid").innerHTML = list.length ? list.map((a) => `
      <button class="dex-card" data-open="${a.id}">
        ${pic(a, "dex-pic")}
        <div class="dex-info">
          <span class="dex-num">${num(a.id)}</span>
          <h5>${esc(a.nom)}</h5>
          <div class="badges">${badges(a)}</div>
        </div>
      </button>`).join("") : `<p class="empty">Aucun animal ne correspond à ta recherche.</p>`;
  }

  /* ─────────────── Fiche détaillée ─────────────── */
  function segBar(label, v) {
    const on = Math.round(v / 100 * 15);
    return `<div class="seg"><ul>${Array.from({ length: 15 }, (_, i) => `<li class="${14 - i < on ? "on" : ""}"></li>`).join("")}</ul><span>${label}</span></div>`;
  }
  function openDetail(id) {
    const a = byId(id);
    if (!a) return;
    const prev = byId(a.id === 1 ? ANIMALS.length : a.id - 1), next = byId(a.id === ANIMALS.length ? 1 : a.id + 1);
    const mil = ["Terre", "Eau", "Air"];
    $("#detailBody").innerHTML = `
      <div class="dt-nav">
        <button data-open="${prev.id}"><span>‹</span> ${num(prev.id)} ${esc(prev.nom)}</button>
        <button data-open="${next.id}">${esc(next.nom)} ${num(next.id)} <span>›</span></button>
      </div>
      <h2 id="detailTitle" class="dt-title">${esc(a.nom)} <span>${num(a.id)}</span></h2>
      <div class="dt-grid">
        <div>
          ${pic(a, "dt-pic")}
          <div class="dt-stats">
            <h4>Stats de base</h4>
            <div class="segs">
              ${segBar("Attaque", a.att)}${segBar("Défense", a.def)}${segBar("Agilité", a.agi)}
              ${segBar("Endurance", a.end)}${segBar("Intell.", a.int)}${segBar("Vitesse", Engine.speedScore(a.kmh))}
            </div>
          </div>
        </div>
        <div>
          <p class="dt-fact">${esc(a.fait)}</p>
          <div class="dt-info">
            <div><span>Nom scientifique</span><b><i>${esc(a.sci)}</i></b></div>
            <div><span>Classe</span><b>${a.classe}</b></div>
            <div><span>Poids</span><b>${Engine.fmtKg(a.kg)}</b></div>
            <div><span>Taille</span><b>${a.taille.toLocaleString("fr-FR")} m</b></div>
            <div><span>Vitesse max</span><b>${a.kmh} km/h</b></div>
            <div><span>Talent</span><b>${esc(a.talent)}</b></div>
            <div class="wide"><span>Armes</span><b>${esc(a.arme)}</b></div>
          </div>
          <h4 class="dt-h">Habitat</h4>
          <div class="badges">${badges(a)}</div>
          <h4 class="dt-h">Aisance selon le terrain</h4>
          <div class="milieu">${a.milieu.map((m, i) => `<div><span>${mil[i]}</span><div class="mbar"><i style="width:${m * 100}%"></i></div></div>`).join("")}</div>
          <h4 class="dt-h">Armes spéciales</h4>
          <p class="dt-special">
            Venin : <b>${a.venin}/3</b>${a.passif ? " (défensif)" : ""}${a.electrique ? " (électrique)" : ""} ·
            Armure : <b>${a.armure}/3</b>
            ${a.rv ? ` · Résistance au venin : <b>${Math.round(a.rv * 100)} %</b>` : ""}
          </p>
          <div class="dt-actions">
            <button class="btn-corner red" data-corner="A" data-id="${a.id}">Envoyer au coin rouge</button>
            <button class="btn-corner blue" data-corner="B" data-id="${a.id}">Envoyer au coin bleu</button>
          </div>
        </div>
      </div>`;
    openModal("#detailModal");
    paintImages();
  }

  /* ─────────────── Sélecteur de combattant ─────────────── */
  let pickSlot = "A";
  function openPicker(slot) {
    pickSlot = slot;
    $("#pickTitle").innerHTML = `Choisis le combattant du <span class="${slot === "A" ? "red" : "blue"}">${slot === "A" ? "coin rouge" : "coin bleu"}</span>`;
    $("#pickSearch").value = "";
    renderPicker();
    openModal("#pickModal");
    setTimeout(() => $("#pickSearch").focus(), 50);
  }
  function renderPicker() {
    const list = filterList($("#pickSearch").value, $("#pickClasse").value, "");
    const other = state[pickSlot === "A" ? "B" : "A"];
    $("#pickGrid").innerHTML = list.map((a) => `
      <button class="pick-card ${a.id === state[pickSlot] ? "sel" : ""}" data-pick="${a.id}">
        ${pic(a)}
        <span class="pick-name">${esc(a.nom)}</span>
        ${a.id === other ? `<span class="pick-tag">adversaire</span>` : ""}
      </button>`).join("") || `<p class="empty">Aucun résultat.</p>`;
  }

  /* ─────────────── Fenêtres ─────────────── */
  function openModal(sel) {
    const m = $(sel);
    m.hidden = false;
    document.body.classList.add("noscroll");
  }
  function closeModals() {
    $$(".modal").forEach((m) => (m.hidden = true));
    document.body.classList.remove("noscroll");
  }

  /* ─────────────── Événements ─────────────── */
  function bind() {
    document.addEventListener("click", (ev) => {
      const t = ev.target;
      const open = t.closest("[data-open]");
      if (open) { openDetail(open.dataset.open); return; }
      if (t.closest("[data-close]")) { closeModals(); return; }
      const corner = t.closest("[data-corner]");
      if (corner) {
        state[corner.dataset.corner] = +corner.dataset.id;
        closeModals(); renderSlots(); paintImages();
        $("#arene").scrollIntoView({ behavior: "smooth" });
        return;
      }
      const pick = t.closest("[data-pick]");
      if (pick) { state[pickSlot] = +pick.dataset.pick; closeModals(); renderSlots(); paintImages(); return; }
      const slot = t.closest(".corner");
      if (slot) openPicker(slot.dataset.slot);
    });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeModals(); });

    $$("#terrainPick button").forEach((b) => b.onclick = () => setTerrain(b.dataset.t));
    $("#fightBtn").onclick = () => fight();
    $("#swapBtn").onclick = () => { [state.A, state.B] = [state.B, state.A]; renderSlots(); paintImages(); };
    $("#randomBtn").onclick = () => {
      const i = Math.floor(Math.random() * ANIMALS.length);
      let j = Math.floor(Math.random() * (ANIMALS.length - 1));
      if (j >= i) j++;
      state.A = ANIMALS[i].id; state.B = ANIMALS[j].id;
      setTerrain("auto"); renderSlots(); paintImages(); fight();
    };

    ["#dexSearch", "#fClasse", "#fHabitat", "#fSort"].forEach((s) => $(s).addEventListener("input", () => { renderDex(); paintImages(); }));
    $("#dexGo").onclick = () => { renderDex(); paintImages(); };
    $("#globalSearch").addEventListener("keydown", (ev) => {
      if (ev.key !== "Enter") return;
      $("#dexSearch").value = ev.target.value;
      renderDex(); paintImages();
      $("#dex").scrollIntoView({ behavior: "smooth" });
    });
    ["#pickSearch", "#pickClasse"].forEach((s) => $(s).addEventListener("input", () => { renderPicker(); paintImages(); }));
    $("#pickSearch").addEventListener("keydown", (ev) => {
      if (ev.key !== "Enter") return;
      const first = $("#pickGrid [data-pick]");
      if (first) first.click();
    });

    $("#burger").onclick = () => $("#navlinks").classList.toggle("open");
    $$("#navlinks a").forEach((l) => l.addEventListener("click", () => $("#navlinks").classList.remove("open")));
  }

  function fillSelects() {
    const opts = (arr) => arr.map((x) => `<option>${x}</option>`).join("");
    $("#fClasse").insertAdjacentHTML("beforeend", opts(CLASSES));
    $("#pickClasse").insertAdjacentHTML("beforeend", opts(CLASSES));
    $("#fHabitat").insertAdjacentHTML("beforeend", opts(Object.keys(HABITATS)));
  }

  function init() {
    fillSelects();
    renderCarousel();
    renderLegends();
    renderDex();
    bind();
    const p = new URLSearchParams(location.search);
    if (byId(p.get("a")) && byId(p.get("b"))) {
      state.A = +p.get("a"); state.B = +p.get("b");
      if (["auto", "terre", "eau", "air"].includes(p.get("t"))) setTerrain(p.get("t"));
      renderSlots(); fight(false);
    } else {
      renderSlots();
    }
    loadImages();
  }
  init();
})();
