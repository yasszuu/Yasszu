# Histoires d'animaux · Ép. 1 — Le retour du loup en France

Vidéo 1080×1920, ~83 s, DA satellite (même moteur que `../v2`).

Chapitres : accroche (globe) → 1. la disparition (XVIIIe → années 1930) → 2. le refuge italien
(Apennins, protection 1971, trajet jusqu'au Mercantour) → 3. le retour (5 nov. 1992) →
4. la reconquête (frise 1992 → 2025, départements, compteur) → 5. le conflit (prédation, déclassement 2025) → outro.

## Pipeline
1. `python3 audio.py` – voix off (Piper `fr_FR-tom-medium`), timeline partagée, bruitages (hurlements synthétisés,
   pas, tampon, impacts…) et musique 84 BPM par sections
2. `sh mix.sh` – mixage + normalisation -14 LUFS
3. `node build.js` – page autonome `loup.html` (jouable avec le son)
4. `sh sheet.sh planche.jpg 5 20 40` – planche d'aperçu à des instants donnés
5. Rendu : `node render_par.js <début> <fin>` dans 4 terminaux, puis
   `ffmpeg -framerate 30 -i frames/%05d.jpg -i mix.wav -c:v libx264 -pix_fmt yuv420p -crf 20 -c:a aac -shortest le-retour-du-loup.mp4`

Textures : copier `../v2/tex_world.jpg` et `../v2/tex_europe.jpg` ici. Voix : dossier `vits-piper-fr_FR-tom-medium`
(release sherpa-onnx `tts-models`).

## Sources des faits
- Population : OFB / Réseau Loup-Lynx, estimation 2025 = 1 082 (IC 95 % : 989 – 1 187) ; 2024 = 1 013
- Retour : 5 novembre 1992, vallon de Mollières (Valdeblore), parc national du Mercantour ; recolonisation naturelle depuis l'Italie
- Disparition : années 1930 ; Italie : ~100 loups dans les Apennins, protégé dès 1971
- Fronts : Massif central 1997, Pyrénées-Orientales 1999, Jura 2003, Vosges ; Bretagne / Normandie aujourd'hui (FERUS, DREAL)
- Prédation 2024 : ~12 000 animaux (bilan provisoire) ; statut abaissé « strictement protégé » → « protégé » en 2025 (Berne + UE)
- La carte des départements par année est **simplifiée** (fronts de colonisation), pas un relevé officiel.
