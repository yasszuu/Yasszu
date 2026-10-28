const ALONG = (pts, k, z, ease=LIN) => [view(...along(pts, k), z), ease];
const KEYS = [
  [0.0,   view(22, 47, 4.3)],
  [1.3,   view(20, 50, 4.75), EO],
  [2.1,   view(19.4, 52.0, 5.7), EX],                         // la Pologne
  [Ed("w02") + 0.2, view(19.6, 52.1, 6.0), LIN],
  [S("w03") + 0.6, view(24, 44, 3.95), EX],                   // tout le voyage
  [Ed("w03"), view(24, 44, 4.1), LIN],
  [S("w04") + 0.5, view(53, 33, 5.0), EX],                    // Iran 1942
  [Ed("w04"), view(52.5, 33.5, 5.15), LIN],
  [M("w05", 0.3), view(51, 37, 5.6), E],
  [Ed("w05"), view(50.6, 36.6, 5.75), LIN],
  [M("w06", 0.2), view(48.7, 35, 6.1), E],                    // Hamadan
  [Ed("w08"), view(48.4, 34.85, 6.45), LIN],
  [S("w09") + 0.2, view(...HAMADAN, 5.4), E],                 // Irak, Syrie, Palestine, Égypte
  [HITS9[0], view(...along(R_LAND, LAND_T[1][1]), 5.4), LIN],
  [HITS9[1], view(...along(R_LAND, LAND_T[2][1]), 5.45), LIN],
  [HITS9[2], view(...along(R_LAND, LAND_T[3][1]), 5.5), LIN],
  [HITS9[3], view(30.4, 31.1, 5.6), LIN],
  [S("w10") + 0.5, view(26, 34, 5.0), E],                     // la traversée vers l'Italie
  [M("w10", 0.75), view(...along(R_SEA1, 0.5), 5.1), LIN],
  [M("w11", 0.2), view(...along(R_SEA1, 0.82), 5.3), LIN],
  [M("w11", 0.65), view(14.3, 40.9, 5.7), LIN],
  [Ed("w11"), view(14.2, 41.0, 5.9), LIN],
  [S("w12") + 0.6, view(...CASSINO, 7.4), EX],                // Mont-Cassin
  [Ed("w13"), view(13.82, 41.5, 7.85), LIN],
  [Ed("w14"), view(13.9, 41.6, 7.5), LIN],
  [S("w15") + 0.4, view(8, 41, 4.4), EX],                     // vers l'Écosse
  [M("w15", 0.55), view(-8.5, 46, 4.45), LIN],
  [Ed("w15") + 0.1, view(-4.4, 55.6, 5.4), E],
  [S("w16") + 0.5, view(...EDIN, 7.0), EX],                   // zoo d'Édimbourg
  [Ed("w17"), view(-3.2, 55.95, 7.45), LIN],
  [S("w18") + 0.6, view(8, 53, 4.75), EX],                    // statues : Écosse et Pologne
  [Ed("w18"), view(8.5, 53, 4.95), LIN],
  [DUR, view(9, 53, 5.2), LIN],
];
