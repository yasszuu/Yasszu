# Notes de production (préférences validées)

- **Voix** : ElevenLabs (Multilingual v2), script avec `<break time="1.5s" />` entre répliques ; mp3 déposé dans le dossier Google Drive **CLAUDE**.
- **Cris d'animaux** : jamais synthétisés → demander à l'utilisateur un vrai enregistrement (dossier Drive CLAUDE).
- **Images d'animaux** : détourées (PNG/WebP transparents), envoyées dans le chat ou sur le Drive.
- **DA** : style « Culture G » — ouverture directement zoomée + recul / demi-tour du globe vers le lieu ; imagerie satellite vive
  (`lion/grade.py`) ; textes blancs ombrés + jaune `#ffd60a` ; pas de source en bas de l'écran.
- **Pas de pastilles / badges ronds pleins** (ex. le rond jaune « ≈ 300 KG ») : chiffres en gros texte blanc/jaune ombré, comme le reste.
- **Mix** : bruitages et musique à -50 % sous la voix, -14 LUFS.
- Durée ≥ 1 min 01.
- **Police unique : Montserrat** (Black / ExtraBold) pour TOUS les textes. Pas de police arrondie (Lilita One refusée).
- **Bruitage d'ouverture** (whoosh synthétisé) jugé moche → ne plus synthétiser les whooshes / transitions ;
  demander à l'utilisateur un pack de vrais bruitages (whoosh, pop, impact…) ou s'en passer.
- **Symboles, icônes, schémas** (mini-animaux, bateau, virus, etc.) : ne pas les dessiner soi-même.
  Prévenir l'utilisateur AVANT, avec la liste exacte, pour qu'il les génère et les envoie (PNG détourés).
- Ne pas empiler plusieurs textes cinétiques en même temps au même endroit (ex. « 600 millions / 100 millions / résistants »).
- **Ouverture** : toujours un plan carte (jamais une photo en premier).
- **Flou de vitesse** : fort en zoom avant, très léger en zoom arrière.
- **Sous-titres** : GROS (≈ 84 px), EN HAUT de l'écran, par groupes de 2–3 mots ; le titre n'apparaît que pendant l'accroche.
- **Photos plein écran** : ponctuelles (~2 s), toujours amenées par une plongée « ultra-zoom » sur la carte + flash.
- **Motion design carte** : multiplier zooms, focus (assombrir hors du pays), ultra-zooms, balayages le long d'un fleuve / d'une route.
- **Pas d'ultra-zoom** au-delà de l'échelle régionale (imagerie Natural Earth ~1,8 km/pixel → flou). Pour une vraie plongée
  « Google Maps », demander à l'utilisateur un clip Google Earth Studio (mention « Google Earth » visible).
- **Pas de photo en ouverture** : la première minute d'accroche reste sur la carte ; les animaux y apparaissent en PNG détourés.
- **Flou de mouvement très léger** sur les balayages/rotations du globe et les zooms (ne pas abuser) — l'image doit rester nette.
- **Trajets dessinés sur la carte** : montrer l'origine et le parcours de l'animal (lignes animées pays → pays avec dates) avant d'arriver en France.
- **Zoom maximum** : ouverture au niveau « continent » (comme la vidéo Afrique du Sud d'ishak-geo), lieu **entouré / pingé** — jamais de gros zoom pixelisé. Ailleurs, ne pas dépasser ~1,6× la vue France entière.
- **Cri / bruit de l'animal uniquement dans l'intro** (sinon dérangeant).
- **Pas de textes encadrés (« chips ») en bas de l'écran** : sous-titres en haut + textes cinétiques suffisent ; compteurs en texte simple.
- **Animaux passagers clandestins** (bateau, pneu, camion…) : montrer clairement l'animal à l'intérieur (il vole/entre dans l'objet, puis reste visible sur le véhicule avec halo).
- **Plans 3D Blender (style « maquette » validé, démo `demo-3d-arctique.mp4`)** : 2-3 plans par vidéo aux moments forts ; formes simples low-poly, couleurs franches, animal = forme 3D rouge vif sans détail ; caméra qui suit le sujet, profondeur de champ. Éviter la surexposition (lumière un peu plus douce que la démo).
- **Pas de Terre entière / d'espace visible** : rester à l'échelle pays/continent (globe plus grand que l'écran), beaucoup de mouvement
  (caméra qui suit l'animal, balayages, zooms). Exception rare : illustrer un tour du monde ou la distance Terre-Lune.
