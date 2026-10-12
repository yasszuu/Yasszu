# Histoires d'animaux · Ép. 2 — Le lion de l'Atlas

Vidéo 1080×1920, ~1 min 52, voix ElevenLabs. Nouvelle DA « satellite vif » façon Culture G :
ouverture directement zoomée (Asie), recul + demi-tour du globe, plongée sur le Maroc.

## Pipeline
1. `python3 grade.py full` – textures vives (Natural Earth I + fonds marins HYP, étalonnage désert / cultures / forêts)
   → `tex_world.jpg`, `tex_region.jpg` (Afrique du Nord + Europe, 120 px/°). Rasters : `NE1_HR_LC_SR_W_DR`, `HYP_HR_SR_OB_DR`.
2. `VO_FILE=voix-lion.mp3 python3 audio.py` – découpe la voix (pauses de 1,5 s), timeline, bruitages
   (rugissement, avion, déclic photo, coup de feu, foule, tampon…), musique en mode hijaz avec percussions
3. `sh mix.sh` – mixage (bruitages et musique à -50 %), -14 LUFS
4. `node build.js` puis `sh sheet.sh planche.jpg 5 30 60` pour les aperçus
5. Rendu : `node render_par.js <début> <fin>` × 4, puis ffmpeg sur `frames/`

## Sources des faits
- Aire historique du Maroc à l'Égypte, crinière jusqu'au ventre, poids rapportés par les chasseurs du XIXe (270–300 kg, peu fiables) : Wikipédia (Barbary lion), Britannica
- Captures romaines pour les arènes ; dernier lion sauvage abattu en 1942 près de Taddert (Tizi n'Tichka) : Wikipédia (Lion de l'Atlas)
- Photo aérienne de 1925 (Marcelin Flandrin, vol Casablanca–Dakar)
- Ménagerie royale (lions offerts aux sultans) → zoo de Rabat, plus grand groupe au monde ; < 100 en captivité ; pureté génétique débattue (études PMC5021484, PMC8714086)
- 4 lionceaux nés en Tchéquie en 2025, pistes de réintroduction : TelQuel, 7 août 2025
