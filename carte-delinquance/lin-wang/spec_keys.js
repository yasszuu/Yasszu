const KEYS = [
  [0.0,   view(112, 26, 4.1)],
  [1.3,   view(119, 25, 4.9), EO],
  [2.2,   view(121.0, 24.3, 6.0), EX],                        // Taïwan en deuil
  [Ed("l02"), view(121.2, 24.6, 6.4), LIN],
  [S("l03") + 0.6, view(106, 24.5, 4.15), EX],                // tout le voyage : Birmanie → Canton → Taïwan
  [Ed("l03"), view(106, 24.5, 4.3), LIN],
  [S("l04") + 0.6, view(96.8, 26.2, 6.0), EX],                // 1943 : la jungle de Birmanie
  [S("l05") + 0.2, view(96.9, 26.0, 6.2), LIN],
  [M("l05", 0.38), view(116, 28, 3.7), EX],                   // l'armée japonaise
  [M("l05", 0.95), view(114, 27, 3.85), LIN],
  [S("l06") + 0.5, view(96.6, 26.4, 6.3), EX],                // les troupes chinoises attaquent depuis Ledo
  [Ed("l07"), view(96.9, 26.0, 6.8), LIN],
  [S("l08") + 0.5, view(99.5, 25.2, 5.6), EX],                // le retour à pied
  [CL.a + 0.4, view(101.5, 25.0, 5.4), LIN],
  [CL.b - 0.3, view(103.5, 24.8, 5.3), LIN],
  [M("l10", 0.62), view(112.6, 23.3, 5.9), E],                // Canton
  [Ed("l10"), view(113.0, 23.2, 6.1), LIN],
  [SHIP[0], view(115.5, 22.8, 5.9), E],                       // le bateau vers Taïwan
  [SHIP[1], view(119.8, 22.9, 6.1), LIN],
  [Ed("l11") + 0.2, view(120.6, 23.4, 6.3), E],
  [Ed("l12"), view(120.5, 23.2, 6.6), LIN],
  [S("l13") + 0.6, view(...TAIPEI, 7.7), EX],                 // zoo de Taipei
  [Ed("l14"), view(121.53, 25.04, 8.1), LIN],
  [S("l15") + 0.5, view(121.55, 25.03, 8.7), EX],             // le déménagement, en parade
  [Ed("l15"), view(121.56, 25.02, 9.0), LIN],
  [S("l16") + 0.6, view(120.9, 23.75, 6.25), EX],             // 2003 : tout Taïwan
  [Ed("l17"), view(120.9, 23.75, 6.5), LIN],
  [DUR, view(120.95, 23.8, 6.7), LIN],
];
