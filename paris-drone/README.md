# Paris — drone shot (motion design 3D)

Vidéo verticale 1080×1920, 12 s, 30 fps : vol de drone rapide dans un boulevard haussmannien,
remontée au-dessus d'une place puis descente/zoom jusqu'à un homme sur son téléphone.

Scène 100 % procédurale (Three.js) : ~4 500 immeubles haussmanniens (balcons filants, lucarnes,
toits en zinc, cheminées), tour Eiffel, voitures, piétons, arbres, fontaine, colonne Morris,
pigeons, HUD de drone animé et écran de téléphone synchronisé avec la distance du drone.

## Rendu

```bash
npm install
node render.mjs                                  # -> paris-drone.mp4
node render.mjs --frames 0,120,359 --scale 0.5   # images de test dans stills/
```
