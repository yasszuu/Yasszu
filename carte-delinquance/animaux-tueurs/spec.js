// ------------------------------------------------------------------ lieux
const UP = [81.6, 27.6], TZ = [35.0, -6.2], NG = [8.1, 9.6], INDC = [78.5, 22.5];
const LAKES = [[33.0, -1.0], [36.35, -0.77], [29.6, -6.2], [34.6, -12.0], [28.0, -17.0], [32.5, 15.6], [22.6, -19.2], [31.4, 3.5]];
const HOT = [UP, TZ, [33, -1], INDC, NG];
const ENT = ["t2", "t3", "t4", "t5", "t6"];
const T_CRY = k => TL.cries.find(c => c.id === k).t;
const near2 = (n, a, b) => SFX(n).find(x => x >= a && x <= b);
const T_OU = near2("impact", S("t1"), Ed("t1")), T_200 = near2("impact", S("t3"), Ed("t3")), T_500 = near2("impact", S("t4"), Ed("t4"));
const T_59 = near2("impact", S("t5"), Ed("t5")), T_700 = near2("impact", S("t6"), Ed("t6")), T_IND2 = near2("pop", M("t5", 0.7), Ed("t5") + 0.2), T_NG = near2("pop", M("t6", 0.7), Ed("t6") + 0.2);
const POPS_L = SFX("pop").filter(x => x > M("t4", 0.55) && x < Ed("t4") + 0.5);
// ------------------------------------------------------------------ caméra
const mx = lon => (lon + 180)/360*TS;
const my = lat => { const r = lat*Math.PI/180; return (1 - Math.log(Math.tan(r) + 1/Math.cos(r))/Math.PI)/2*TS; };
const view = (lon, lat, z, dy=-90) => [mx(lon), my(lat) - dy/2**z, W/2**z];
const KEYS = [
  [0.0,  view(70, 18, 3.3)],
  [1.2,  view(45, 8, 3.6), EO],
  [Ed("t1"), view(42, 8, 3.75), LIN],
  [S("t2") + 1.0, view(45, 10, 3.6), LIN],
  [S("t2") + 1.8, view(80, 22, 4.6), EX],                 // N°5 loup : Inde
  [Ed("t2") + 0.3, view(...UP, 5.9), E],
  [S("t3") + 0.9, view(76, 20, 5.2), LIN],
  [S("t3") + 1.7, view(35, -4, 4.6), EX],                 // N°4 lion : Tanzanie
  [Ed("t3") + 0.3, view(35, -6, 5.3), E],
  [S("t4") + 0.9, view(34, -5, 5.1), LIN],
  [S("t4") + 1.7, view(29, -3, 4.1), EX],                 // N°3 hippo : lacs et fleuves d'Afrique
  [Ed("t4") + 0.3, view(30, -5, 4.35), LIN],
  [S("t5") + 0.9, view(30, -3, 4.2), LIN],
  [S("t5") + 1.7, view(55, 8, 3.45), EX],                 // N°2 chien : Inde + Afrique
  [M("t5", 0.85), view(58, 10, 3.6), LIN],
  [Ed("t5") + 0.3, view(...INDC, 4.6), E],
  [S("t6") + 0.9, view(76, 20, 4.4), LIN],
  [S("t6") + 1.7, view(15, 2, 3.85), EX],                 // N°1 moustique : Afrique, Nigeria
  [M("t6", 0.82), view(14, 4, 4.0), LIN],
  [Ed("t6") + 0.3, view(...NG, 5.2), E],
  [S("t7") + 0.6, view(35, 8, 3.6), EX],
  [DUR, view(36, 8, 3.75), LIN],
];
