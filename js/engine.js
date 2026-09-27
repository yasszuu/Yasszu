/*
 * Moteur de duel : calcule un score de combat pour chaque animal sur un terrain
 * donné, en déduit une probabilité de victoire, puis génère les explications.
 */
(function () {
  const TERRAINS = {
    terre: { idx: 0, nom: "Terre ferme", emoji: "🌿" },
    eau:   { idx: 1, nom: "En pleine eau", emoji: "🌊" },
    air:   { idx: 2, nom: "Dans les airs", emoji: "☁️" }
  };

  const W = { att: 0.34, def: 0.24, agi: 0.14, end: 0.10, int: 0.08, vit: 0.10 };
  const MASS_PER_DECADE = 18; // points gagnés à chaque fois que la masse est multipliée par 10
  const SPREAD = 14;          // plus c'est grand, plus les résultats sont incertains

  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const speedScore = (kmh) => clamp(Math.log10(kmh + 1) / Math.log10(391) * 100, 0, 100);

  // ── Aides grammaticales ──
  const lower = (a) => a.nom.charAt(0).toLowerCase() + a.nom.slice(1);
  const elide = (a) => /^[aeiouyéèêâîôûh]/i.test(a.nom) && !/^(Harpie|Hyène)/.test(a.nom);
  const le = (a) => elide(a) ? "l'" + lower(a) : (a.g === "f" ? "la " : "le ") + lower(a);
  const Le = (a) => { const s = le(a); return s.charAt(0).toUpperCase() + s.slice(1); };
  const de = (a) => elide(a) ? "de l'" + lower(a) : (a.g === "f" ? "de la " : "du ") + lower(a);
  const a_ = (a) => elide(a) ? "à l'" + lower(a) : (a.g === "f" ? "à la " : "au ") + lower(a);
  const low = (s) => s.charAt(0).toLowerCase() + s.slice(1);
  const e = (a) => a.g === "f" ? "e" : "";
  const gw = (a, m, f) => a.g === "f" ? f : m;

  function fmtKg(kg) {
    if (kg >= 1000) return (kg / 1000).toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " t";
    if (kg >= 1) return kg.toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " kg";
    return (kg * 1000).toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " g";
  }
  function fmtRatio(r) {
    if (r >= 1000) return Math.round(r).toLocaleString("fr-FR");
    if (r >= 10) return Math.round(r).toString();
    return r.toLocaleString("fr-FR", { maximumFractionDigits: 1 });
  }

  function autoTerrain(a, b) {
    let best = "terre", bestVal = -1;
    for (const key of ["terre", "eau", "air"]) {
      const i = TERRAINS[key].idx;
      const v = Math.min(a.milieu[i], b.milieu[i]);
      if (v > bestVal + 1e-9) { best = key; bestVal = v; }
    }
    return best;
  }

  function venomBonus(a, b) {
    if (!a.venin) return 0;
    const sizeF = clamp(1 - (Math.log10(b.kg) - 2.3) / 3, 0.1, 1);   // un venin tue moins vite un géant
    const armorF = a.electrique ? 1 : 1 - 0.28 * b.armure;               // l'électricité ignore la carapace
    const dodgeF = 1 - Math.max(0, b.agi - 60) / 100;                    // les plus vifs esquivent
    const passF = a.passif ? 0.55 : 1;                                   // toxine défensive
    return a.venin * 15 * sizeF * armorF * (1 - b.rv) * dodgeF * passF;
  }

  function specialist(a, b) {
    return a.bat.some((t) => b.tags.includes(t)) ? 18 : 0;
  }

  function score(a, b, terrain) {
    const vit = speedScore(a.kmh);
    const parts = {
      att: a.att * W.att, def: a.def * W.def, agi: a.agi * W.agi,
      end: a.end * W.end, int: a.int * W.int, vit: vit * W.vit,
      masse: MASS_PER_DECADE * (Math.log10(a.kg) + 4),
      venin: venomBonus(a, b),
      special: specialist(a, b)
    };
    const raw = Object.values(parts).reduce((s, x) => s + x, 0);
    const env = a.milieu[TERRAINS[terrain].idx];
    const total = raw * (0.3 + 0.7 * env);
    return { parts, raw, env, total, terrainDelta: total - raw, vit };
  }

  function duel(a, b, terrainChoice) {
    const auto = !terrainChoice || terrainChoice === "auto";
    const terrain = auto ? autoTerrain(a, b) : terrainChoice;
    const sA = score(a, b, terrain), sB = score(b, a, terrain);
    const pA = a.id === b.id ? 0.5 : 1 / (1 + Math.exp(-(sA.total - sB.total) / SPREAD));
    const winner = pA >= 0.5 ? a : b, loser = winner === a ? b : a;
    const pW = Math.max(pA, 1 - pA);
    const sW = winner === a ? sA : sB, sL = winner === a ? sB : sA;

    // ── Facteurs décisifs (positif = avantage A) ──
    const massRatio = a.kg >= b.kg ? a.kg / b.kg : b.kg / a.kg;
    const heavy = a.kg >= b.kg ? a : b, light = heavy === a ? b : a;
    const F = [];
    const push = (key, label, val, desc) => F.push({ key, label, val, desc });
    push("masse", "Masse", sA.parts.masse - sB.parts.masse,
      a.kg === b.kg ? "Même poids." : `${Le(heavy)} pèse ${fmtRatio(massRatio)} fois plus lourd (${fmtKg(heavy.kg)} contre ${fmtKg(light.kg)}).`);
    push("att", "Attaque", sA.parts.att - sB.parts.att, `${a.att} contre ${b.att} : puissance des morsures, griffes, cornes ou coups.`);
    push("def", "Défense", sA.parts.def - sB.parts.def, `${a.def} contre ${b.def} : cuir, carapace et capacité à encaisser.`);
    push("agi", "Agilité", sA.parts.agi - sB.parts.agi, `${a.agi} contre ${b.agi} : réflexes et capacité d'esquive.`);
    push("vit", "Vitesse", sA.parts.vit - sB.parts.vit, `${a.kmh} km/h contre ${b.kmh} km/h en pointe.`);
    push("end", "Endurance", sA.parts.end - sB.parts.end, `${a.end} contre ${b.end} : qui tient le plus longtemps.`);
    push("int", "Intelligence", sA.parts.int - sB.parts.int, `${a.int} contre ${b.int} : ruse, stratégie, lecture du combat.`);
    if (sA.parts.venin || sB.parts.venin)
      push("venin", a.electrique || b.electrique ? "Venin / électricité" : "Venin", sA.parts.venin - sB.parts.venin, venomText(a, b, sA, sB));
    if (sA.parts.special || sB.parts.special) {
      const s = sA.parts.special ? a : b, t = s === a ? b : a;
      push("special", "Spécialiste", sA.parts.special - sB.parts.special, `${Le(s)} est un${e(s)} spécialiste de ce genre d'adversaire : ${le(t)} fait partie de ses proies ou ennemis naturels.`);
    }
    push("terrain", "Terrain", sA.terrainDelta - sB.terrainDelta,
      `${TERRAINS[terrain].nom} : aisance de ${Math.round(sA.env * 100)} % pour ${le(a)} contre ${Math.round(sB.env * 100)} % pour ${le(b)}.`);
    F.sort((x, y) => Math.abs(y.val) - Math.abs(x.val));

    return {
      a, b, terrain, auto, sA, sB, pA, pB: 1 - pA, winner, loser, pW,
      factors: F.filter((f) => Math.abs(f.val) >= 0.5),
      story: story(a, b, terrain, auto, sA, sB, winner, loser, pW, sW, sL),
      verdict: verdict(winner, loser, pW, sW, sL, terrain)
    };
  }

  function venomText(a, b, sA, sB) {
    const out = [];
    for (const [x, y, s] of [[a, b, sA], [b, a, sB]]) {
      if (!x.venin) continue;
      let t = `${Le(x)} ${x.electrique ? "électrocute" : x.passif ? "est toxique au contact" : "injecte un venin de niveau " + x.venin + "/3"}`;
      const self = [], other = [];
      if (y.rv >= 0.5) self.push("y est quasi insensible");
      if (y.agi >= 85) self.push("esquive très bien");
      if (y.armure >= 2 && !x.electrique) other.push(`sa protection limite les piqûres`);
      if (y.kg > 1000) other.push(`sa masse dilue le venin`);
      const reasons = (self.length ? [`${le(y)} ${self.join(" et ")}`] : []).concat(other);
      out.push(t + (reasons.length ? `, mais ${reasons.join(" et ")}` : "") + ` (+${s.parts.venin.toFixed(0)} pts).`);
    }
    return out.join(" ");
  }

  function story(a, b, terrain, auto, sA, sB, W_, L, pW, sW, sL) {
    const P = [];
    if (a.id === b.id) {
      P.push({ t: "Le miroir", x: `Deux ${lower(a)}s face à face : mêmes armes, mêmes forces. Ce genre de duel se règle sur l'expérience et un peu de chance. Dans la nature, ce type d'affrontement survient surtout pour un territoire ou une femelle.` });
      return P;
    }
    // 1. Le décor
    const T = TERRAINS[terrain];
    let decor = auto
      ? `Terrain choisi automatiquement : ${T.nom.toLowerCase()} ${T.emoji}, l'endroit où ces deux animaux ont le plus de chances de se croiser.`
      : `Le duel se déroule ${terrain === "terre" ? "sur la terre ferme" : terrain === "eau" ? "en pleine eau" : "dans les airs"} ${T.emoji}.`;
    for (const [x, s] of [[a, sA], [b, sB]]) {
      if (s.env < 0.15) decor += ` ${Le(x)} est complètement hors de son élément : ${x.g === "f" ? "elle" : "il"} ne peut quasiment pas se battre ici.`;
      else if (s.env < 0.5) decor += ` ${Le(x)} n'est pas à l'aise dans ce milieu et perd une grande partie de ses moyens.`;
    }
    if (sA.env >= 0.9 && sB.env >= 0.9) decor += " Les deux combattants sont parfaitement dans leur élément.";
    P.push({ t: "Le décor", x: decor });

    // 2. L'approche
    const initA = (a.agi + sA.vit + a.int) / 3, initB = (b.agi + sB.vit + b.int) / 3;
    const fast = initA >= initB ? a : b, slow = fast === a ? b : a;
    let appr;
    if (Math.abs(initA - initB) < 5) appr = `Les deux adversaires se jaugent longuement : aucun n'a un réel avantage de vivacité. ${Le(a)} (${a.kmh} km/h) et ${le(b)} (${b.kmh} km/h) tournent l'un autour de l'autre.`;
    else appr = `Plus ${gw(fast, "vif", "vive")} et plus ${gw(fast, "malin", "maligne")}, ${le(fast)} prend l'initiative. Son atout « ${fast.talent} » lui permet de choisir le moment de l'attaque, tandis que ${le(slow)} doit réagir.`;
    if (fast.int >= 85) appr += ` Très intelligent${e(fast)}, ${le(fast)} cherche l'angle mort de son adversaire plutôt que de charger tête baissée.`;
    P.push({ t: "L'approche", x: appr });

    // 3. Le choc
    const heavy = a.kg >= b.kg ? a : b, light = heavy === a ? b : a;
    const ratio = heavy.kg / light.kg;
    let choc = `${Le(a)} attaque avec ses armes : ${low(a.arme)}. ${Le(b)} riposte : ${low(b.arme)}.`;
    if (ratio >= 20) choc += ` Mais la différence de gabarit est énorme : ${le(heavy)} pèse ${fmtRatio(ratio)} fois plus lourd. Pour ${le(light)}, c'est comme affronter une montagne.`;
    else if (ratio >= 3) choc += ` Avec ${fmtKg(heavy.kg)} contre ${fmtKg(light.kg)}, ${le(heavy)} a un net avantage de masse à chaque impact.`;
    else choc += ` Les gabarits sont proches (${fmtKg(a.kg)} contre ${fmtKg(b.kg)}) : c'est la technique qui fera la différence.`;
    for (const [x, y, s] of [[a, b, sA], [b, a, sB]]) {
      if (!x.venin) continue;
      if (s.parts.venin >= 20) choc += ` Le venin est la carte maîtresse ${de(x)} : une seule touche peut suffire à terrasser ${le(y)}.`;
      else if (s.parts.venin > 0) choc += ` ${Le(x)} tente d'utiliser son ${x.electrique ? "arme électrique" : "venin"}, mais contre ${le(y)} l'effet reste limité.`;
      else choc += ` ${Le(x)} compte sur son ${x.electrique ? "arme électrique" : "venin"}… qui n'a presque aucun effet sur ${le(y)}.`;
    }
    for (const [x, y, s] of [[a, b, sA], [b, a, sB]])
      if (s.parts.special) choc += ` ${Le(x)} connaît parfaitement ce genre d'adversaire : l'affronter fait partie de sa vie.`;
    if (a.armure >= 3 || b.armure >= 3) {
      const t = a.armure >= b.armure ? a : b;
      choc += ` La protection ${de(t)} (${t.def} en défense) rend chaque attaque difficile à faire passer.`;
    }
    P.push({ t: "Le choc", x: choc });

    // 4. Le dénouement
    let fin;
    if (pW >= 0.9) fin = `Domination écrasante. ${Le(W_)} prend rapidement le dessus et l'emporte dans l'immense majorité des cas.`;
    else if (pW >= 0.7) fin = `Victoire nette ${de(W_)}, mais pas sans risque : ${le(L)} peut infliger de sérieuses blessures avant de céder.`;
    else if (pW >= 0.55) fin = `Combat très serré ! ${Le(W_)} a un léger avantage, mais une seule erreur peut tout renverser.`;
    else fin = `C'est quasiment pile ou face : les deux animaux ont des chances presque égales.`;
    fin += ` La meilleure carte ${de(L)} : « ${L.talent} ».`;
    if (L.kmh > W_.kmh * 1.3 && sL.env >= 0.5 && pW >= 0.6)
      fin += ` Dans la réalité, ${le(L)}, plus rapide (${L.kmh} km/h contre ${W_.kmh}), choisirait sans doute la fuite plutôt que le combat.`;
    P.push({ t: "Le dénouement", x: fin });
    return P;
  }

  function verdict(W_, L, pW, sW, sL) {
    if (W_.id === L.id) return "Match nul : c'est un combat miroir.";
    const pct = Math.round(pW * 100);
    if (pW >= 0.97) return `${Le(W_)} gagne quasiment à tous les coups (${pct} %).`;
    if (pW >= 0.8) return `${Le(W_)} l'emporte largement (${pct} % de chances).`;
    if (pW >= 0.6) return `${Le(W_)} est ${gw(W_, "favori", "favorite")} (${pct} % de chances).`;
    return `Avantage très léger pour ${le(W_)} (${pct} %).`;
  }

  window.Engine = { duel, TERRAINS, speedScore, fmtKg, autoTerrain, le, Le, de };
})();
