// ------------------------------------------------------------------ lieux
const SG = [103.82, 1.355], MERLION = [103.8545, 1.2868], RIVER = [103.851, 1.2885], GIR = [70.8, 21.15];
const R_PRINCE = [[104.47, 0.98], [104.36, 1.1], [104.15, 1.2], [103.98, 1.255], [103.851, 1.2885]];
const NOCAP = ["s01", "s02", "s08"];
// ------------------------------------------------------------------ calendrier
const pops = (k, a=0, b=1) => SFX("pop").filter(x => x >= M(k, a) - 0.05 && x <= M(k, b) + 0.05);
const [T_SINGA, T_PURA] = pops("s01"), T_EQ = near("impact", M("s01", 0.5), Ed("s01")), T_ZERO = near("hit", S("s02"), Ed("s02"));
const T_FLAG = pops("s03")[0], T_FAUVE = pops("s04")[0], T_REVEAL = near("hit", M("s04", 0.6), Ed("s04")), PRINCE = [M("s04", 0.2), M("s04", 0.58)];
const T_GIR = near("impact", M("s05", 0.5), Ed("s05")), ARC = [M("s05", 0.25), T_GIR - 0.05], T_TIGRE = near("impact", S("s06"), Ed("s06"));
const T_MER = pops("s07")[0], [T_CTA1, T_CTA2] = pops("s08");
const KEYS = [
  [0.0,   view(100, 8, 2.9)],
  [1.4,   view(103, 3, 4.2), EO],
  [S("s01") + 2.0, view(103.82, 1.345, 11.0), EX],              // plongée sur l'île
  [Ed("s02"), view(103.82, 1.35, 11.35), LIN],
  [S("s03") + 0.1, view(103.82, 1.36, 10.85), E],
  [S("s04") + 0.9, view(103.84, 1.34, 10.6), LIN],
  [PRINCE[0] + 0.3, view(104.17, 1.17, 9.25), E],               // le détroit, le prince arrive de Bintan
  [PRINCE[1], view(104.0, 1.24, 9.6), LIN],
  [T_FAUVE, view(103.86, 1.295, 11.2), E],                      // embouchure de la rivière
  [Ed("s04"), view(103.855, 1.29, 11.5), LIN],
  [S("s05") + 0.9, view(88, 11.5, 4.25), EX],                   // jusqu'en Inde
  [Ed("s05"), view(86.5, 12, 4.45), LIN],
  [S("s06") + 0.7, view(103.83, 1.35, 10.0), EX],               // retour à Singapour
  [Ed("s06") + 0.3, view(103.84, 1.34, 10.3), LIN],
  [T_MER, view(...MERLION, 13.1), E],                           // le Merlion aujourd'hui
  [Ed("s07") + 0.3, view(MERLION[0] + 0.001, MERLION[1], 13.3), LIN],
  [DUR, view(103.84, 1.33, 10.6), E],
];
