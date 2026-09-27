# Duel Sauvage 🐾

Site web où l'on choisit deux animaux parmi **100 espèces réelles** pour découvrir qui gagnerait un duel dans la nature, avec stats, facteurs décisifs et récit du combat.
La direction artistique s'inspire de pokemon.com (bandeaux sombres, panneau blanc rayé, onglets, badges de couleur, fiches façon Pokédex).

## Lancer le site

Aucune installation : c'est du HTML/CSS/JS pur.

```bash
python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```

(On peut aussi ouvrir `index.html` directement, ou publier le dépôt avec GitHub Pages.)

## Fonctionnalités

- **Arène** : coin rouge contre coin bleu, choix du terrain (Auto / Terre / Eau / Ciel), duel aléatoire. L'URL permet de partager un duel.
- **Résultat** : probabilité de victoire, face-à-face des stats, facteurs décisifs (masse, attaque, venin, terrain…) et déroulé du combat en 4 phases.
- **Animalédex** : les 100 animaux, avec recherche, filtres par classe et par habitat, tris, et une fiche détaillée pour chacun.
- **Duels légendaires** : les affrontements classiques (lion contre tigre, orque contre grand requin blanc, mangouste contre cobra…).
- Photos chargées automatiquement depuis Wikipédia (emoji affiché en secours si le chargement échoue).

## Structure

- `js/data.js` : les 100 animaux (poids, vitesse, stats, venin, armure, milieu, armes, talent, anecdote)
- `js/engine.js` : le moteur de duel et la génération des explications
- `js/app.js` : l'interface
- `css/style.css` : le style
