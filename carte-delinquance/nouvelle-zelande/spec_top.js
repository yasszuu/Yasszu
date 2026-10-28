// ------------------------------------------------------------------ lieux
const NZ = [173.2, -41.2], FARM = [176.62, -39.72];
const NOCAP = ["n01", "n05"];
// ------------------------------------------------------------------ calendrier
const pops = (k, a=0, b=1) => SFX("pop").filter(x => x >= M(k, a) - 0.05 && x <= M(k, b) + 0.05);
const T_22 = M("n01", 0.45), T_HAB = near("impact", M("n01", 0.8), Ed("n01") + 0.2), T_FLAG = pops("n02")[0], T_HUM = M("n02", 0.3), T_MOU = M("n02", 0.62);
const T_COIN = M("n03", 0.45), T_PLUS = near("hit", M("n03", 0.6), Ed("n03")), T_DOWN = M("n04", 0.45), T_4 = pops("n04")[0];
const [T_CTA1, T_CTA2] = pops("n05");
const KEYS = [
  [0.0,   view(178, -36, 3.0)],
  [1.35,  view(174, -40, 4.3), EO],
  [S("n01") + 1.5, view(173.4, -40.8, 6.45), EX],             // plongée sur la Nouvelle-Zélande
  [Ed("n01"), view(173.3, -40.9, 6.6), LIN],
  [S("n02") + 0.4, view(173.0, -41.1, 6.55), E],
  [Ed("n02"), view(172.9, -41.2, 6.75), LIN],
  [S("n03") + 0.8, view(...FARM, 11.3), EX],                    // collines à moutons (Hawke's Bay)
  [Ed("n03"), view(FARM[0] + 0.01, FARM[1] - 0.01, 11.6), LIN],
  [S("n04") + 0.7, view(173.0, -41.1, 6.55), EX],
  [Ed("n04"), view(173.0, -41.2, 6.7), LIN],
  [DUR, view(173.1, -41.0, 6.95), LIN],
];
