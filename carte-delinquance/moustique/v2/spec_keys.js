const FRV = (z=6.6, dl=0, db=0) => view(2.4 + dl, 46.4 + db, z);
const T_JUMP = Ed("m09") + 0.05;
const KEYS = [
  [0.0,   view(12, 49, 4.5)],
  [0.5,   view(8, 47.5, 5.0), EO],
  [1.35,  FRV(6.45), EX],                                   // whip sur la France
  [M("m01", 0.42), FRV(6.7, 0.8, -0.5), LIN],
  [M("m01", 0.58), view(7.45, 43.9, 8.7), EX],              // plongée sur Menton
  [Ed("m01") + 0.2, view(7.5, 43.82, 9.0), LIN],
  [S("m02") + 0.55, FRV(6.5), EX],                          // 80 départements
  [Ed("m02"), FRV(6.8), LIN],
  [S("m03") + 0.5, view(-1.5, 46.8, 7.4), EX],              // balayage ouest → est
  [M("m03", 0.55), view(6.5, 45.4, 7.4), E],
  [Ed("m03"), FRV(6.55), EX],
  [S("m04") + 0.9, view(SEA[0], SEA[1], 5.0), EX],          // Asie du Sud-Est
  [Ed("m04"), view(SEA[0] - 1, SEA[1] - 1, 5.3), LIN],
  [Ed("m05"), view(SEA[0] - 2, SEA[1] - 2, 5.6), LIN],
  [S("m06") + 0.6, view(110, 16, 4.6), EX],
  [Ed("m06"), view(108, 14, 4.85), LIN],
  [M("m07", 0.45), view(105, 12, 5.0), LIN],
  [M("m07", 0.6), view(85, 15, 3.0), EX],                   // routes maritimes du monde
  [Ed("m07") + 0.2, view(80, 15, 3.2), LIN],
  ...routeKeys(ROUTES[0]),                                  // 1979 Albanie
  [Ed("m08"), view(19.6, 41.2, 6.2), EX],
  ...routeKeys(ROUTES[1]),                                  // 1985 Texas
  [Ed("m09"), view(264.6, 29.8, 5.6), EX],
  [T_JUMP, view(-95.4, 29.8, 5.6), LIN],                    // même vue, longitude ramenée dans [-180, 180]
  ...routeKeys(ROUTES[2]),                                  // 1990 Gênes
  [Ed("m10"), view(...GENES, 7.6), EX],
  [S("m11") + 0.5, view(8.9, 44.35, 8.6), E],               // la côte ligure jusqu'à Menton
  [M("m11", 0.8), view(7.52, 43.8, 8.8), LIN],
  [Ed("m11"), view(7.5, 43.8, 9.0), LIN],
  [S("m12") + 0.5, FRV(6.45), EX],                          // résistent au froid
  [Ed("m12"), FRV(6.7), LIN],
  [S("m13") + 0.5, view(5.3, 43.6, 7.6), EX],               // vallée du Rhône (camion)
  [M("m13", 0.92), view(4.85, 45.6, 7.7), LIN],
  [S("m14") + 0.5, view(0.2, 44.3, 7.2), EX],               // Sud-Ouest
  [M("m14", 0.62), view(2.6, 46.2, 7.1), E],                // centre
  [S("m15") + 0.4, view(...PARIS, 8.2), EX],                // région parisienne
  [Ed("m15"), view(PARIS[0], PARIS[1], 8.45), LIN],
  [S("m16") + 0.5, FRV(6.5), EX],                           // 81 départements
  [Ed("m16"), FRV(6.8), LIN],
  [Ed("m17"), FRV(6.95, 0.6, -0.6), LIN],
  [S("m18") + 0.45, view(4.6, 44.0, 7.2), EX],              // dengue, chikungunya
  [Ed("m18"), view(4.2, 44.1, 7.4), LIN],
  [S("m19") + 0.45, view(3.6, 44.4, 6.95), EX],             // 800 cas
  [Ed("m19"), view(3.6, 44.6, 7.25), LIN],
  [S("m20") + 0.5, FRV(6.45), EX],
  [DUR, FRV(6.85), LIN],
];
